import io
from contextlib import redirect_stdout
from typing import Iterator

import pytest

from rusttt import constants as const
from rusttt import logic


def bitboard_from_squares(*squares: int) -> int:
    mask = 0
    for square in squares:
        mask |= const.SQUARE_BBS[square]
    return mask


def clear_board() -> None:
    for idx in range(len(logic.piece_array)):
        logic.piece_array[idx] = 0


@pytest.fixture(autouse=True)
def reset_globals() -> Iterator[None]:
    piece_snapshot = logic.piece_array.copy()
    castle_snapshot = logic.castle_rights.copy()
    white_turn = logic.white_to_play
    en_passant = logic.ep
    ply = logic.board_ply
    yield
    logic.piece_array[:] = piece_snapshot
    logic.castle_rights[:] = castle_snapshot
    logic.white_to_play = white_turn
    logic.ep = en_passant
    logic.board_ply = ply


def test_bitscan_forward_single_bit_matches_index():
    for index, mask in enumerate(const.SQUARE_BBS):
        if index >= 64:
            break
        assert logic.bitscan_forward(mask) == index


def test_bitscan_forward_returns_lowest_set_bit():
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
    assert logic.piece_array[const.WN] == const.WN_STARTING_POSITIONS
    assert logic.piece_array[const.WB] == const.WB_STARTING_POSITIONS
    assert logic.piece_array[const.WR] == const.WR_STARTING_POSITIONS
    assert logic.piece_array[const.WQ] == const.WQ_STARTING_POSITION
    assert logic.piece_array[const.WK] == const.WK_STARTING_POSITION
    assert logic.piece_array[const.BP] == const.BP_STARTING_POSITIONS
    assert logic.piece_array[const.BN] == const.BN_STARTING_POSITIONS
    assert logic.piece_array[const.BB] == const.BB_STARTING_POSITIONS
    assert logic.piece_array[const.BR] == const.BR_STARTING_POSITIONS
    assert logic.piece_array[const.BQ] == const.BQ_STARTING_POSITION
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


def test_get_occupied_index_finds_piece_identifier() -> None:
    clear_board()
    logic.piece_array[const.WQ] = const.SQUARE_BBS[const.E4]
    assert logic.get_occupied_index(const.E4) == const.WQ


def test_get_occupied_index_returns_empty_when_no_piece() -> None:
    clear_board()
    assert logic.get_occupied_index(const.E4) == const.EMPTY


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


def test_get_rook_moves_separate_stops_at_first_blocker_in_file() -> None:
    blockers = const.SQUARE_BBS[const.E6]
    expected = bitboard_from_squares(
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
    assert logic.get_rook_moves_separate(const.E4, blockers) == expected


def test_get_rook_moves_separate_stops_at_blocker_on_rank() -> None:
    blockers = const.SQUARE_BBS[const.C4]
    expected = bitboard_from_squares(
        const.E8,
        const.E7,
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


def test_get_bishop_moves_separate_respects_blocker_diagonal() -> None:
    blockers = const.SQUARE_BBS[const.F7]
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
        const.A2,
        const.G2,
        const.H1,
    )
    assert logic.get_bishop_moves_separate(const.D5, blockers) == expected


def test_get_bishop_moves_separate_respects_blocker_down_diagonal() -> None:
    blockers = const.SQUARE_BBS[const.C4]
    expected = bitboard_from_squares(
        const.A8,
        const.G8,
        const.B7,
        const.F7,
        const.C6,
        const.E6,
        const.C4,
        const.E4,
        const.F3,
        const.G2,
        const.H1,
    )
    assert logic.get_bishop_moves_separate(const.D5, blockers) == expected


def test_is_square_attacked_by_black_detects_pawn() -> None:
    clear_board()
    logic.piece_array[const.BP] = const.SQUARE_BBS[const.F5]
    occupancy = const.SQUARE_BBS[const.F5]
    assert logic.is_square_attacked_by_black(const.E4, occupancy) is True


def test_is_square_attacked_by_black_detects_knight() -> None:
    clear_board()
    logic.piece_array[const.BN] = const.SQUARE_BBS[const.F5]
    occupancy = const.SQUARE_BBS[const.F5]
    assert logic.is_square_attacked_by_black(const.E7, occupancy) is True


def test_is_square_attacked_by_black_detects_bishop() -> None:
    clear_board()
    logic.piece_array[const.BB] = const.SQUARE_BBS[const.B7]
    occupancy = const.SQUARE_BBS[const.B7]
    assert logic.is_square_attacked_by_black(const.E4, occupancy) is True


def test_is_square_attacked_by_black_detects_rook() -> None:
    clear_board()
    logic.piece_array[const.BR] = const.SQUARE_BBS[const.E8]
    occupancy = const.SQUARE_BBS[const.E8]
    assert logic.is_square_attacked_by_black(const.E4, occupancy) is True


def test_is_square_attacked_by_black_detects_queen_on_file() -> None:
    clear_board()
    logic.piece_array[const.BQ] = const.SQUARE_BBS[const.E8]
    occupancy = const.SQUARE_BBS[const.E8]
    assert logic.is_square_attacked_by_black(const.E4, occupancy) is True


def test_is_square_attacked_by_white_detects_pawn() -> None:
    clear_board()
    logic.piece_array[const.WP] = const.SQUARE_BBS[const.E4]
    occupancy = const.SQUARE_BBS[const.E4]
    assert logic.is_square_attacked_by_white(const.F5, occupancy) is True


def test_is_square_attacked_by_white_detects_knight() -> None:
    clear_board()
    logic.piece_array[const.WN] = const.SQUARE_BBS[const.F3]
    occupancy = const.SQUARE_BBS[const.F3]
    assert logic.is_square_attacked_by_white(const.E5, occupancy) is True


def test_is_square_attacked_by_white_detects_bishop() -> None:
    clear_board()
    logic.piece_array[const.WB] = const.SQUARE_BBS[const.B2]
    occupancy = const.SQUARE_BBS[const.B2]
    assert logic.is_square_attacked_by_white(const.E5, occupancy) is True


def test_is_square_attacked_by_white_detects_rook() -> None:
    clear_board()
    logic.piece_array[const.WR] = const.SQUARE_BBS[const.E1]
    occupancy = const.SQUARE_BBS[const.E1]
    assert logic.is_square_attacked_by_white(const.E5, occupancy) is True


def test_is_square_attacked_by_white_detects_queen_diagonal() -> None:
    clear_board()
    logic.piece_array[const.WQ] = const.SQUARE_BBS[const.B2]
    occupancy = const.SQUARE_BBS[const.B2]
    assert logic.is_square_attacked_by_white(const.E5, occupancy) is True


def test_is_square_attacked_reports_false_when_no_attackers() -> None:
    clear_board()
    occupancy = 0
    assert logic.is_square_attacked_by_black(const.E4, occupancy) is False
    assert logic.is_square_attacked_by_white(const.E5, occupancy) is False


def test_print_board_outputs_expected_metadata() -> None:
    logic.set_starting_position()
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        logic.print_board()
    output = buffer.getvalue()
    assert "Board:" in output
    assert "White to play: True" in output
    assert "ep:" in output
    assert "ply:" in output


def test_perft_inline_depth_one_starting_position() -> None:
    logic.set_starting_position()
    assert logic.perft_inline(1, 0) == 20
