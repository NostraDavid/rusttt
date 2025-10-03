import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from rusttt import constants as const
from rusttt import logic


def bitboard_from_squares(*squares: int) -> int:
    mask = 0
    for square in squares:
        mask |= const.SQUARE_BBS[square]
    return mask


def square_mask(square: int) -> int:
    return const.SQUARE_BBS[square]


def iter_squares(bitboard: int):
    while bitboard:
        lsb = bitboard & -bitboard
        yield (lsb.bit_length() - 1)
        bitboard ^= lsb


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


def combined_occupancy(piece_array: list[int]) -> int:
    occ = 0
    for mask in piece_array:
        occ |= mask
    return occ


def naive_square_attacked_by_white(piece_array: list[int], occupancy: int, square: int) -> bool:
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


def naive_square_attacked_by_black(piece_array: list[int], occupancy: int, square: int) -> bool:
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


@pytest.fixture(autouse=True)
def reset_globals():
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


bitboard_strategy = st.integers(min_value=0, max_value=(1 << 64) - 1)
non_zero_bitboard_strategy = st.integers(min_value=1, max_value=(1 << 64) - 1)
square_strategy = st.integers(min_value=0, max_value=63)


@settings(deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(bitboard=non_zero_bitboard_strategy)
def test_bitscan_forward_matches_lowest_bit(bitboard: int):
    expected = (bitboard & -bitboard).bit_length() - 1
    assert logic.bitscan_forward(bitboard) == expected


@settings(deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(square=square_strategy, occupancy=bitboard_strategy)
def test_get_rook_moves_matches_naive(square: int, occupancy: int):
    expected = naive_rook_attacks(square, occupancy)
    assert logic.get_rook_moves_separate(square, occupancy) == expected


@settings(deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(square=square_strategy, occupancy=bitboard_strategy)
def test_get_bishop_moves_matches_naive(square: int, occupancy: int):
    expected = naive_bishop_attacks(square, occupancy)
    assert logic.get_bishop_moves_separate(square, occupancy) == expected


@st.composite
def board_position_strategy(draw):
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


@settings(deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(piece_array=board_position_strategy(), square=square_strategy)
def test_white_attack_detection_matches_naive(piece_array: list[int], square: int):
    occupancy = combined_occupancy(piece_array)
    logic.piece_array[:] = piece_array
    assert logic.is_square_attacked_by_white(square, occupancy) == naive_square_attacked_by_white(
        piece_array, occupancy, square
    )


@settings(deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(piece_array=board_position_strategy(), square=square_strategy)
def test_black_attack_detection_matches_naive(piece_array: list[int], square: int):
    occupancy = combined_occupancy(piece_array)
    logic.piece_array[:] = piece_array
    assert logic.is_square_attacked_by_black(square, occupancy) == naive_square_attacked_by_black(
        piece_array, occupancy, square
    )
