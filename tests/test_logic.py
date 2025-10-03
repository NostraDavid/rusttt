from __future__ import annotations

from typing import Dict, Iterable, Iterator, List

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from rusttt import constants as const
from rusttt import logic


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def bitboard_from_squares(*squares: int) -> int:
    mask = 0
    for square in squares:
        mask |= const.SQUARE_BBS[square]
    return mask


def square_mask(square: int) -> int:
    return const.SQUARE_BBS[square]


def iter_squares(bitboard: int) -> Iterator[int]:
    while bitboard:
        lsb = bitboard & -bitboard
        yield (lsb.bit_length() - 1)
        bitboard ^= lsb


def clear_board() -> None:
    for idx in range(len(logic.piece_array)):
        logic.piece_array[idx] = 0


def empty_piece_array() -> List[int]:
    return [0] * 12


def set_piece(bitboards: List[int], piece: int, *squares: int) -> None:
    mask = 0
    for square in squares:
        mask |= square_mask(square)
    bitboards[piece] = mask


def add_piece(bitboards: List[int], piece: int, square: int) -> None:
    bitboards[piece] |= square_mask(square)


def load_position(
    pieces: Dict[int, Iterable[int]],
    *,
    white_to_play: bool = True,
    castle_rights: List[bool] | None = None,
    en_passant: int = const.NO_SQUARE,
) -> None:
    clear_board()
    for piece, squares in pieces.items():
        mask = 0
        for square in squares:
            mask |= square_mask(square)
        logic.piece_array[piece] = mask

    if castle_rights is None:
        castle_rights = [False, False, False, False]

    logic.castle_rights[:] = castle_rights
    logic.white_to_play = white_to_play
    logic.ep = en_passant


def combined_occupancy(piece_array: List[int]) -> int:
    occ = 0
    for mask in piece_array:
        occ |= mask
    return occ


def white_occupancy(piece_array: List[int]) -> int:
    occ = 0
    for idx in range(const.WP, const.WK + 1):
        occ |= piece_array[idx]
    return occ


def black_occupancy(piece_array: List[int]) -> int:
    occ = 0
    for idx in range(const.BP, const.BK + 1):
        occ |= piece_array[idx]
    return occ


def naive_rook_attacks(square: int, occupancy: int) -> int:
    attacks = 0

    current = square
    while current >= 8:
        current -= 8
        attacks |= square_mask(current)
        if occupancy & square_mask(current):
            break

    current = square
    while current <= 55:
        current += 8
        attacks |= square_mask(current)
        if occupancy & square_mask(current):
            break

    current = square
    while current % 8 != 7:
        current += 1
        attacks |= square_mask(current)
        if occupancy & square_mask(current):
            break

    current = square
    while current % 8 != 0:
        current -= 1
        attacks |= square_mask(current)
        if occupancy & square_mask(current):
            break

    return attacks


def naive_bishop_attacks(square: int, occupancy: int) -> int:
    attacks = 0

    current = square
    while current >= 8 and current % 8 != 0:
        current -= 9
        attacks |= square_mask(current)
        if occupancy & square_mask(current):
            break

    current = square
    while current >= 8 and current % 8 != 7:
        current -= 7
        attacks |= square_mask(current)
        if occupancy & square_mask(current):
            break

    current = square
    while current <= 55 and current % 8 != 0:
        current += 7
        attacks |= square_mask(current)
        if occupancy & square_mask(current):
            break

    current = square
    while current <= 55 and current % 8 != 7:
        current += 9
        attacks |= square_mask(current)
        if occupancy & square_mask(current):
            break

    return attacks


def naive_square_attacked_by_white(piece_array: List[int], occupancy: int, square: int) -> bool:
    target = square_mask(square)

    for pawn_square in iter_squares(piece_array[const.WP]):
        if const.WHITE_PAWN_ATTACKS[pawn_square] & target:
            return True

    for knight_square in iter_squares(piece_array[const.WN]):
        if const.KNIGHT_ATTACKS[knight_square] & target:
            return True

    for bishop_square in iter_squares(piece_array[const.WB]):
        if naive_bishop_attacks(bishop_square, occupancy) & target:
            return True

    for rook_square in iter_squares(piece_array[const.WR]):
        if naive_rook_attacks(rook_square, occupancy) & target:
            return True

    for queen_square in iter_squares(piece_array[const.WQ]):
        if naive_bishop_attacks(queen_square, occupancy) & target:
            return True
        if naive_rook_attacks(queen_square, occupancy) & target:
            return True

    for king_square in iter_squares(piece_array[const.WK]):
        if const.KING_ATTACKS[king_square] & target:
            return True

    return False


def naive_square_attacked_by_black(piece_array: List[int], occupancy: int, square: int) -> bool:
    target = square_mask(square)

    for pawn_square in iter_squares(piece_array[const.BP]):
        if const.BLACK_PAWN_ATTACKS[pawn_square] & target:
            return True

    for knight_square in iter_squares(piece_array[const.BN]):
        if const.KNIGHT_ATTACKS[knight_square] & target:
            return True

    for bishop_square in iter_squares(piece_array[const.BB]):
        if naive_bishop_attacks(bishop_square, occupancy) & target:
            return True

    for rook_square in iter_squares(piece_array[const.BR]):
        if naive_rook_attacks(rook_square, occupancy) & target:
            return True

    for queen_square in iter_squares(piece_array[const.BQ]):
        if naive_bishop_attacks(queen_square, occupancy) & target:
            return True
        if naive_rook_attacks(queen_square, occupancy) & target:
            return True

    for king_square in iter_squares(piece_array[const.BK]):
        if const.KING_ATTACKS[king_square] & target:
            return True

    return False


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_globals() -> Iterator[None]:
    piece_snapshot = logic.piece_array.copy()
    castle_snapshot = logic.castle_rights.copy()
    white_turn = logic.white_to_play
    en_passant = logic.ep
    ply = logic.board_ply
    original_bitscan = logic.bitscan_forward
    python_bitscan = getattr(logic.bitscan_forward, "py_func", logic.bitscan_forward)
    logic.bitscan_forward = python_bitscan
    try:
        yield
    finally:
        logic.piece_array[:] = piece_snapshot
        logic.castle_rights[:] = castle_snapshot
        logic.white_to_play = white_turn
        logic.ep = en_passant
        logic.board_ply = ply
        logic.bitscan_forward = original_bitscan


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


bitboard_strategy = st.integers(min_value=0, max_value=(1 << 64) - 1)
non_zero_bitboard_strategy = st.integers(min_value=1, max_value=(1 << 64) - 1)
square_strategy = st.integers(min_value=0, max_value=63)


@st.composite
def board_position_strategy(draw) -> List[int]:
    placements = draw(
        st.lists(
            st.tuples(st.integers(min_value=0, max_value=11), square_strategy),
            unique_by=lambda item: item[1],
            max_size=16,
        )
    )
    piece_array = [0] * 12
    for piece, square in placements:
        piece_array[piece] |= square_mask(square)
    return piece_array


# ---------------------------------------------------------------------------
# Deterministic unit tests
# ---------------------------------------------------------------------------


def test_bitscan_forward_single_bit_matches_index() -> None:
    for index, mask in enumerate(const.SQUARE_BBS[:64]):
        assert logic.bitscan_forward(mask) == index


def test_bitscan_forward_returns_lowest_set_bit() -> None:
    bitboard = const.SQUARE_BBS[10] | const.SQUARE_BBS[27] | const.SQUARE_BBS[42]
    assert logic.bitscan_forward(bitboard) == 10


def test_print_move_no_nl_basic_move(capsys: pytest.CaptureFixture[str]) -> None:
    logic.print_move_no_nl(const.E2, const.E4, const.TAG_NONE)
    captured = capsys.readouterr()
    assert captured.out == "e2e4"


def test_print_move_no_nl_knight_promotion_suffix(capsys: pytest.CaptureFixture[str]) -> None:
    logic.print_move_no_nl(const.A7, const.A8, const.TAG_W_KNIGHT_PROMOTION)
    captured = capsys.readouterr()
    assert captured.out == "a7a8n"


def test_set_starting_position_initializes_globals() -> None:
    logic.set_starting_position()
    assert logic.white_to_play is True
    assert logic.ep == const.NO_SQUARE
    assert logic.castle_rights == [True, True, True, True]
    assert logic.piece_array[const.WP] == const.WP_STARTING_POSITIONS
    assert logic.piece_array[const.BK] == const.BK_STARTING_POSITION


def test_board_initial_state() -> None:
    board = logic.Board()
    assert board.piece_array == [0] * 12
    assert board.white_to_play is True
    assert board.castle_rights == [True, True, True, True]
    assert board.ep == const.NO_SQUARE


def test_set_starting_position_struct_matches_globals() -> None:
    board = logic.Board()
    logic.set_starting_position_struct(board)
    assert board.piece_array[const.WP] == const.WP_STARTING_POSITIONS
    assert board.piece_array[const.BP] == const.BP_STARTING_POSITIONS
    assert board.white_to_play is True
    assert board.castle_rights == [True, True, True, True]
    assert board.ep == const.NO_SQUARE


def test_is_occupied_checks_bitboard_membership() -> None:
    assert logic.is_occupied(const.SQUARE_BBS[const.E4], const.E4) is True
    assert logic.is_occupied(const.SQUARE_BBS[const.E4], const.D4) is False


def test_get_occupied_index_identifies_piece() -> None:
    clear_board()
    logic.piece_array[const.WQ] = const.SQUARE_BBS[const.E4]
    assert logic.get_occupied_index(const.E4) == const.WQ


def test_get_occupied_index_returns_empty_when_square_free() -> None:
    clear_board()
    assert logic.get_occupied_index(const.E4) == const.EMPTY


def test_pin_mask_for_square_returns_ray_mask() -> None:
    king = const.E1
    pins = [logic.Pin(pinned_square=const.E2, pinner_square=const.E8)]
    expected = const.INBETWEEN_BITBOARDS[king][const.E8]
    assert logic.pin_mask_for_square(pins, king, const.E2) == expected
    assert logic.pin_mask_for_square(pins, king, const.D2) == logic.MAX_ULONG


def test_locate_captured_piece_identifies_target() -> None:
    clear_board()
    logic.piece_array[const.BQ] = square_mask(const.D4)
    assert logic.locate_captured_piece(const.D4, const.WP) == const.BQ
    assert logic.locate_captured_piece(const.C4, const.WP) == -1


def test_scan_slider_checks_and_pins_detects_check_and_pin() -> None:
    friendly = square_mask(const.E2)
    enemy_rook = square_mask(const.E8)
    check_count, check_mask, pins, pin_lookup = logic.scan_slider_checks_and_pins(
        const.E1,
        enemy_bishop_bb=0,
        enemy_rook_bb=enemy_rook,
        enemy_queen_bb=0,
        friendly_occupancies=friendly,
        enemy_occupancies=enemy_rook,
    )
    assert check_count == 0
    assert pins == [logic.Pin(const.E2, const.E8)]
    assert pin_lookup[const.E2] == const.INBETWEEN_BITBOARDS[const.E1][const.E8]

    check_count, check_mask, pins, pin_lookup = logic.scan_slider_checks_and_pins(
        const.E1,
        enemy_bishop_bb=square_mask(const.H4),
        enemy_rook_bb=0,
        enemy_queen_bb=0,
        friendly_occupancies=0,
        enemy_occupancies=square_mask(const.H4),
    )
    assert check_count == 1
    assert check_mask == const.INBETWEEN_BITBOARDS[const.E1][const.H4]
    assert pins == []


def test_analyze_king_state_detects_rook_check_and_pin() -> None:
    board = empty_piece_array()
    set_piece(board, const.WK, const.E2)
    set_piece(board, const.BR, const.E8)
    add_piece(board, const.WN, const.C4)
    add_piece(board, const.BB, const.B5)

    friendly_occ = white_occupancy(board)
    enemy_occ = black_occupancy(board)

    state = logic.analyze_king_state(board, True, friendly_occ, enemy_occ)
    assert state.king_square == const.E2
    assert state.check_count == 1
    assert state.check_mask == const.INBETWEEN_BITBOARDS[const.E2][const.E8]
    assert logic.Pin(const.C4, const.B5) in state.pins


def test_get_rook_moves_separate_without_blockers() -> None:
    expected = bitboard_from_squares(
        const.E8,
        const.E7,
        const.E6,
        const.E5,
        const.A4,
        const.B4,
        const.C4,
        const.D4,
        const.F4,
        const.G4,
        const.H4,
        const.E3,
        const.E2,
        const.E1,
    )
    assert logic.get_rook_moves_separate(const.E4, 0) == expected


def test_get_rook_moves_separate_stops_at_blockers() -> None:
    blockers = const.SQUARE_BBS[const.C4] | const.SQUARE_BBS[const.E6]
    expected = bitboard_from_squares(
        const.E6,
        const.E5,
        const.C4,
        const.D4,
        const.F4,
        const.G4,
        const.H4,
        const.E3,
        const.E2,
        const.E1,
    )
    assert logic.get_rook_moves_separate(const.E4, blockers) == expected


def test_get_bishop_moves_separate_without_blockers() -> None:
    expected = bitboard_from_squares(
        const.A8,
        const.G8,
        const.B7,
        const.F7,
        const.C6,
        const.E6,
        const.C4,
        const.E4,
        const.B3,
        const.F3,
        const.A2,
        const.G2,
        const.H1,
    )
    assert logic.get_bishop_moves_separate(const.D5, 0) == expected


def test_get_bishop_moves_separate_respects_blockers() -> None:
    blockers = const.SQUARE_BBS[const.F7] | const.SQUARE_BBS[const.B3]
    expected = bitboard_from_squares(
        const.A8,
        const.B7,
        const.F7,
        const.C6,
        const.E6,
        const.C4,
        const.E4,
        const.B3,
        const.F3,
        const.G2,
        const.H1,
    )
    assert logic.get_bishop_moves_separate(const.D5, blockers) == expected


def test_generate_moves_allows_castling_when_path_clear() -> None:
    piece_array = [0] * 12
    piece_array[const.WK] = square_mask(const.E1)
    piece_array[const.WR] = square_mask(const.H1)
    piece_array[const.BK] = square_mask(const.E8)

    white_occ = white_occupancy(piece_array)
    black_occ = black_occupancy(piece_array)
    combined = white_occ | black_occ

    moves = logic.generate_moves_for_side(
        piece_array,
        True,
        [True, True, True, True],
        const.NO_SQUARE,
        white_occ,
        black_occ,
        combined,
    )

    assert logic.Move(const.E1, const.G1, const.TAG_WCASTLEKS, const.WK) in moves


def test_generate_moves_allows_black_castling() -> None:
    piece_array = [0] * 12
    piece_array[const.BK] = square_mask(const.E8)
    piece_array[const.BR] = square_mask(const.H8) | square_mask(const.A8)
    piece_array[const.WK] = square_mask(const.E1)

    white_occ = white_occupancy(piece_array)
    black_occ = black_occupancy(piece_array)
    combined = white_occ | black_occ

    moves = logic.generate_moves_for_side(
        piece_array,
        False,
        [True, True, True, True],
        const.NO_SQUARE,
        white_occ,
        black_occ,
        combined,
    )

    assert logic.Move(const.E8, const.G8, const.TAG_BCASTLEKS, const.BK) in moves
    assert logic.Move(const.E8, const.C8, const.TAG_BCASTLEQS, const.BK) in moves


def test_generate_moves_double_check_limits_to_king_moves() -> None:
    piece_array = [0] * 12
    piece_array[const.WK] = square_mask(const.E1)
    piece_array[const.BR] = square_mask(const.E8)
    piece_array[const.BB] = square_mask(const.B4)

    white_occ = white_occupancy(piece_array)
    black_occ = black_occupancy(piece_array)
    combined = white_occ | black_occ

    moves = logic.generate_moves_for_side(
        piece_array,
        True,
        [False, False, False, False],
        const.NO_SQUARE,
        white_occ,
        black_occ,
        combined,
    )

    assert moves  # at least one escape move
    assert all(move.piece == const.WK for move in moves)


def test_generate_leaper_moves_produces_capture_and_quiet() -> None:
    piece_array = empty_piece_array()
    set_piece(piece_array, const.WN, const.C3)
    king_state = logic.KingState(
        king_square=const.E2,
        check_count=0,
        check_mask=logic.MAX_ULONG,
        pins=[],
        pin_lookup={},
    )
    moves = logic.generate_leaper_moves(
        piece_array[const.WN],
        const.KNIGHT_ATTACKS,
        const.WN,
        enemy_occupancies=square_mask(const.D5),
        empty_occupancies=~0,
        check_mask=logic.MAX_ULONG,
        pins=king_state.pin_lookup,
        king_state=king_state,
    )
    assert logic.Move(const.C3, const.D5, const.TAG_CAPTURE, const.WN) in moves
    assert any(move.tag == const.TAG_NONE for move in moves)


def test_generate_leaper_moves_respects_pin() -> None:
    piece_array = empty_piece_array()
    set_piece(piece_array, const.WN, const.C3)
    king_state = logic.KingState(
        king_square=const.E2,
        check_count=0,
        check_mask=logic.MAX_ULONG,
        pins=[logic.Pin(const.C3, const.C8)],
        pin_lookup={const.C3: const.INBETWEEN_BITBOARDS[const.E2][const.C8]},
    )
    moves = logic.generate_leaper_moves(
        piece_array[const.WN],
        const.KNIGHT_ATTACKS,
        const.WN,
        enemy_occupancies=square_mask(const.D5),
        empty_occupancies=~0,
        check_mask=logic.MAX_ULONG,
        pins=king_state.pin_lookup,
        king_state=king_state,
    )
    assert moves == []


def test_generate_slider_moves_produces_capture_and_quiet() -> None:
    piece_array = empty_piece_array()
    set_piece(piece_array, const.WB, const.C1)
    king_state = logic.KingState(
        king_square=const.E2,
        check_count=0,
        check_mask=logic.MAX_ULONG,
        pins=[],
        pin_lookup={},
    )
    enemy_occ = square_mask(const.H6)
    empty_mask = ~enemy_occ
    moves = logic.generate_slider_moves(
        piece_array[const.WB],
        logic.get_bishop_moves_separate,
        const.WB,
        enemy_occ,
        empty_mask,
        enemy_occ,  # combined with blocker at capture square
        logic.MAX_ULONG,
        king_state.pin_lookup,
        king_state,
    )
    assert logic.Move(const.C1, const.H6, const.TAG_CAPTURE, const.WB) in moves
    assert any(move.tag == const.TAG_NONE for move in moves)


def test_generate_pawn_moves_white_promotion_and_capture() -> None:
    piece_array = empty_piece_array()
    set_piece(piece_array, const.WP, const.A7)
    enemy_occ = square_mask(const.B8)
    combined = enemy_occ | piece_array[const.WP]
    king_state = logic.KingState(const.E1, 0, logic.MAX_ULONG, [], {})
    king_state.pin_lookup = {}
    moves = logic.generate_pawn_moves(
        piece_array,
        True,
        enemy_occ,
        combined,
        logic.MAX_ULONG,
        [],
        king_state,
        const.NO_SQUARE,
    )
    tags = {move.tag for move in moves}
    assert const.TAG_W_QUEEN_PROMOTION in tags
    assert const.TAG_W_CAPTURE_QUEEN_PROMOTION in tags


def test_generate_pawn_moves_black_promotion_capture() -> None:
    piece_array = empty_piece_array()
    set_piece(piece_array, const.BP, const.A2)
    enemy_occ = square_mask(const.B1)
    combined = enemy_occ | piece_array[const.BP]
    king_state = logic.KingState(const.E8, 0, logic.MAX_ULONG, [], {})
    moves = logic.generate_pawn_moves(
        piece_array,
        False,
        enemy_occ,
        combined,
        logic.MAX_ULONG,
        [],
        king_state,
        const.NO_SQUARE,
    )
    tags = {move.tag for move in moves}
    assert const.TAG_B_QUEEN_PROMOTION in tags
    assert const.TAG_B_CAPTURE_QUEEN_PROMOTION in tags


def test_apply_move_double_pawn_sets_ep_and_undo_restores() -> None:
    load_position({const.WP: [const.E2]})
    move = logic.Move(const.E2, const.E4, const.TAG_DOUBLE_PAWN_WHITE, const.WP)

    context = logic.apply_move(move)
    assert logic.piece_array[const.WP] == square_mask(const.E4)
    assert logic.ep == const.E3
    assert logic.white_to_play is False

    logic.undo_move(move, context)
    assert logic.piece_array[const.WP] == square_mask(const.E2)
    assert logic.ep == const.NO_SQUARE
    assert logic.white_to_play is True


def test_apply_move_capture_and_undo_restores_piece() -> None:
    load_position({const.WP: [const.E4], const.BP: [const.D5]})
    move = logic.Move(const.E4, const.D5, const.TAG_CAPTURE, const.WP)

    context = logic.apply_move(move)
    assert logic.piece_array[const.WP] == square_mask(const.D5)
    assert logic.piece_array[const.BP] == 0

    logic.undo_move(move, context)
    assert logic.piece_array[const.WP] == square_mask(const.E4)
    assert logic.piece_array[const.BP] == square_mask(const.D5)


def test_apply_move_white_en_passant_capture_and_undo() -> None:
    load_position({const.WP: [const.E5], const.BP: [const.D5]})
    move = logic.Move(const.E5, const.D6, const.TAG_WHITEEP, const.WP)
    context = logic.apply_move(move)
    assert logic.piece_array[const.WP] == square_mask(const.D6)
    assert logic.piece_array[const.BP] == 0
    logic.undo_move(move, context)
    assert logic.piece_array[const.WP] == square_mask(const.E5)
    assert logic.piece_array[const.BP] == square_mask(const.D5)


def test_apply_move_black_en_passant_capture_and_undo() -> None:
    load_position({const.BP: [const.D4], const.WP: [const.E4]}, white_to_play=False)
    move = logic.Move(const.D4, const.E3, const.TAG_BLACKEP, const.BP)
    context = logic.apply_move(move)
    assert logic.piece_array[const.BP] == square_mask(const.E3)
    assert logic.piece_array[const.WP] == 0
    logic.undo_move(move, context)
    assert logic.piece_array[const.BP] == square_mask(const.D4)
    assert logic.piece_array[const.WP] == square_mask(const.E4)


def test_apply_move_castle_and_undo_restores_state() -> None:
    load_position(
        {
            const.WK: [const.E1],
            const.WR: [const.H1],
            const.BK: [const.E8],
        },
        castle_rights=[True, True, True, True],
    )

    move = logic.Move(const.E1, const.G1, const.TAG_WCASTLEKS, const.WK)

    context = logic.apply_move(move)
    assert logic.piece_array[const.WK] == square_mask(const.G1)
    assert logic.piece_array[const.WR] == square_mask(const.F1)
    assert logic.castle_rights[const.WKS_CASTLE_RIGHTS] is False
    assert logic.castle_rights[const.WQS_CASTLE_RIGHTS] is False

    logic.undo_move(move, context)
    assert logic.piece_array[const.WK] == square_mask(const.E1)
    assert logic.piece_array[const.WR] == square_mask(const.H1)
    assert logic.castle_rights == [True, True, True, True]


def test_apply_move_promotion_and_undo_restores() -> None:
    load_position({const.WP: [const.A7]}, castle_rights=[False, False, False, False])
    move = logic.Move(const.A7, const.A8, const.TAG_W_QUEEN_PROMOTION, const.WP)
    context = logic.apply_move(move)
    assert logic.piece_array[const.WQ] == square_mask(const.A8)
    logic.undo_move(move, context)
    assert logic.piece_array[const.WP] == square_mask(const.A7)
    assert logic.piece_array[const.WQ] == 0


def test_apply_move_capture_promotion_and_undo_restores() -> None:
    load_position({const.WP: [const.A7], const.BN: [const.B8]}, castle_rights=[False, False, False, False])
    move = logic.Move(const.A7, const.B8, const.TAG_W_CAPTURE_ROOK_PROMOTION, const.WP)
    context = logic.apply_move(move)
    assert logic.piece_array[const.WR] == square_mask(const.B8)
    assert logic.piece_array[const.BN] == 0
    logic.undo_move(move, context)
    assert logic.piece_array[const.WP] == square_mask(const.A7)
    assert logic.piece_array[const.BN] == square_mask(const.B8)


def test_apply_move_black_promotion_variants() -> None:
    load_position({const.BP: [const.A2]}, white_to_play=False, castle_rights=[False, False, False, False])
    move = logic.Move(const.A2, const.A1, const.TAG_B_KNIGHT_PROMOTION, const.BP)
    context = logic.apply_move(move)
    assert logic.piece_array[const.BN] == square_mask(const.A1)
    logic.undo_move(move, context)
    assert logic.piece_array[const.BP] == square_mask(const.A2)
    assert logic.piece_array[const.BN] == 0


def test_apply_move_unknown_tag_raises() -> None:
    load_position({const.WP: [const.A2]})
    with pytest.raises(ValueError):
        logic.apply_move(logic.Move(const.A2, const.A3, 99, const.WP))


def test_print_board_outputs_expected_format(capsys: pytest.CaptureFixture[str]) -> None:
    logic.set_starting_position()
    logic.print_board()
    out = capsys.readouterr().out
    assert "Board:" in out
    assert "White to play" in out


def test_perft_inline_depth_one_counts_moves() -> None:
    logic.set_starting_position()
    assert logic.perft_inline(1, 0) > 0


# ---------------------------------------------------------------------------
# Hypothesis property-based tests
# ---------------------------------------------------------------------------


@settings(deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(bitboard=non_zero_bitboard_strategy)
def test_bitscan_forward_matches_lowest_bit(bitboard: int) -> None:
    expected = (bitboard & -bitboard).bit_length() - 1
    assert logic.bitscan_forward(bitboard) == expected


@settings(deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(square=square_strategy, occupancy=bitboard_strategy)
def test_get_rook_moves_matches_naive(square: int, occupancy: int) -> None:
    expected = naive_rook_attacks(square, occupancy)
    assert logic.get_rook_moves_separate(square, occupancy) == expected


@settings(deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(square=square_strategy, occupancy=bitboard_strategy)
def test_get_bishop_moves_matches_naive(square: int, occupancy: int) -> None:
    expected = naive_bishop_attacks(square, occupancy)
    assert logic.get_bishop_moves_separate(square, occupancy) == expected


@settings(deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(piece_array=board_position_strategy(), square=square_strategy)
def test_white_attack_detection_matches_naive(piece_array: List[int], square: int) -> None:
    occupancy = combined_occupancy(piece_array)
    logic.piece_array[:] = piece_array
    assert logic.is_square_attacked_by_white(square, occupancy) == naive_square_attacked_by_white(
        piece_array, occupancy, square
    )


@settings(deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(piece_array=board_position_strategy(), square=square_strategy)
def test_black_attack_detection_matches_naive(piece_array: List[int], square: int) -> None:
    occupancy = combined_occupancy(piece_array)
    logic.piece_array[:] = piece_array
    assert logic.is_square_attacked_by_black(square, occupancy) == naive_square_attacked_by_black(
        piece_array, occupancy, square
    )
