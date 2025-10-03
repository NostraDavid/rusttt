import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import NamedTuple

from rusttt.constants import (
    A1,
    A8,
    BB,
    BB_STARTING_POSITIONS,
    BISHOP_ATTACKS,
    BISHOP_DOWN_LEFT,
    BISHOP_DOWN_RIGHT,
    BISHOP_UP_LEFT,
    BISHOP_UP_RIGHT,
    BK,
    BK_STARTING_POSITION,
    BKS_CASTLE_RIGHTS,
    BKS_EMPTY_BITBOARD,
    BLACK_PAWN_ATTACKS,
    BN,
    BN_STARTING_POSITIONS,
    BP,
    BP_STARTING_POSITIONS,
    BQ,
    BQ_STARTING_POSITION,
    BQS_CASTLE_RIGHTS,
    BQS_EMPTY_BITBOARD,
    BR,
    BR_STARTING_POSITIONS,
    C1,
    C8,
    D1,
    D8,
    E1,
    E8,
    EMPTY,
    F1,
    F8,
    G1,
    G8,
    H1,
    H8,
    INBETWEEN_BITBOARDS,
    KING_ATTACKS,
    KNIGHT_ATTACKS,
    MAX_ULONG,
    NO_SQUARE,
    RANK_2_BITBOARD,
    RANK_4_BITBOARD,
    RANK_5_BITBOARD,
    RANK_7_BITBOARD,
    ROOK_ATTACKS,
    ROOK_DOWN,
    ROOK_LEFT,
    ROOK_RIGHT,
    ROOK_UP,
    SQ_CHAR_X,
    SQ_CHAR_Y,
    SQUARE_BBS,
    TAG_B_BISHOP_PROMOTION,
    TAG_B_CAPTURE_BISHOP_PROMOTION,
    TAG_B_CAPTURE_KNIGHT_PROMOTION,
    TAG_B_CAPTURE_QUEEN_PROMOTION,
    TAG_B_CAPTURE_ROOK_PROMOTION,
    TAG_B_KNIGHT_PROMOTION,
    TAG_B_QUEEN_PROMOTION,
    TAG_B_ROOK_PROMOTION,
    TAG_BCASTLEKS,
    TAG_BCASTLEQS,
    TAG_BLACKEP,
    TAG_CAPTURE,
    TAG_CHECK,
    TAG_CHECK_CAPTURE,
    TAG_DOUBLE_PAWN_BLACK,
    TAG_DOUBLE_PAWN_WHITE,
    TAG_NONE,
    TAG_W_BISHOP_PROMOTION,
    TAG_W_CAPTURE_BISHOP_PROMOTION,
    TAG_W_CAPTURE_KNIGHT_PROMOTION,
    TAG_W_CAPTURE_QUEEN_PROMOTION,
    TAG_W_CAPTURE_ROOK_PROMOTION,
    TAG_W_KNIGHT_PROMOTION,
    TAG_W_QUEEN_PROMOTION,
    TAG_W_ROOK_PROMOTION,
    TAG_WCASTLEKS,
    TAG_WCASTLEQS,
    TAG_WHITEEP,
    WB,
    WB_STARTING_POSITIONS,
    WHITE_PAWN_ATTACKS,
    WK,
    WK_STARTING_POSITION,
    WKS_CASTLE_RIGHTS,
    WKS_EMPTY_BITBOARD,
    WN,
    WN_STARTING_POSITIONS,
    WP,
    WP_STARTING_POSITIONS,
    WQ,
    WQ_STARTING_POSITION,
    WQS_CASTLE_RIGHTS,
    WQS_EMPTY_BITBOARD,
    WR,
    WR_STARTING_POSITIONS,
    piece_colours,
    piece_names,
)

piece_array = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
white_to_play: bool = True
castle_rights: list[bool] = [True, True, True, True]
ep: int = NO_SQUARE
board_ply: int = 0

BOARD_MASK: int = (1 << 64) - 1
BLACK_CAPTURE_RANGE: tuple[int, ...] = tuple(range(BP, BK + 1))
WHITE_CAPTURE_RANGE: tuple[int, ...] = tuple(range(WP, BP))


class Pin(NamedTuple):
    pinned_square: int
    pinner_square: int


class Move(NamedTuple):
    starting: int
    target: int
    tag: int
    piece: int


@dataclass(slots=True)
class KingState:
    king_square: int
    check_count: int
    check_mask: int
    pins: list[Pin]
    pin_lookup: dict[int, int]


@dataclass(slots=True)
class MoveContext:
    captured_piece_index: int
    previous_ep: int
    previous_castle_rights: tuple[bool, bool, bool, bool]


PROMOTION_MAP: dict[int, int] = {
    TAG_W_KNIGHT_PROMOTION: WN,
    TAG_W_BISHOP_PROMOTION: WB,
    TAG_W_ROOK_PROMOTION: WR,
    TAG_W_QUEEN_PROMOTION: WQ,
    TAG_B_KNIGHT_PROMOTION: BN,
    TAG_B_BISHOP_PROMOTION: BB,
    TAG_B_ROOK_PROMOTION: BR,
    TAG_B_QUEEN_PROMOTION: BQ,
}

CAPTURE_PROMOTION_MAP: dict[int, int] = {
    TAG_W_CAPTURE_KNIGHT_PROMOTION: WN,
    TAG_W_CAPTURE_BISHOP_PROMOTION: WB,
    TAG_W_CAPTURE_ROOK_PROMOTION: WR,
    TAG_W_CAPTURE_QUEEN_PROMOTION: WQ,
    TAG_B_CAPTURE_KNIGHT_PROMOTION: BN,
    TAG_B_CAPTURE_BISHOP_PROMOTION: BB,
    TAG_B_CAPTURE_ROOK_PROMOTION: BR,
    TAG_B_CAPTURE_QUEEN_PROMOTION: BQ,
}


def iterate_bits(bitboard: int) -> Iterable[int]:
    """Yield the index of each set bit within ``bitboard``."""

    while bitboard:
        lsb = bitboard & -bitboard
        yield (lsb.bit_length() - 1)
        bitboard ^= lsb


def pin_mask_for_square(
    pins: Sequence[Pin] | Mapping[int, int],
    king_square: int,
    square: int,
) -> int:
    """Return the allowed ray mask for a pinned piece, or ``MAX_ULONG`` if free."""

    if hasattr(pins, "get"):
        return pins.get(square, MAX_ULONG)

    for pin in pins:  # pragma: no cover - compatibility path
        if pin.pinned_square == square:
            return INBETWEEN_BITBOARDS[king_square][pin.pinner_square]

    return MAX_ULONG


def locate_captured_piece(target_square: int, capturing_piece: int) -> int:
    """Return the index of the captured piece for the supplied move."""

    search_range = (
        BLACK_CAPTURE_RANGE if WP <= capturing_piece <= WK else WHITE_CAPTURE_RANGE
    )
    target_mask = SQUARE_BBS[target_square]

    for index in search_range:
        if (piece_array[index] & target_mask) != 0:
            return index

    return -1


def scan_slider_checks_and_pins(
    king_square: int,
    enemy_bishop_bb: int,
    enemy_rook_bb: int,
    enemy_queen_bb: int,
    friendly_occupancies: int,
    enemy_occupancies: int,
) -> tuple[int, int, list[Pin]]:
    """Identify slider-based checks and pins on the supplied king square.

    Returns ``(check_count, check_mask, pins)`` where ``check_mask`` contains the
    squares that must be occupied to block or capture a single checker and
    ``pins`` holds the pinned piece alongside the pinning piece.
    """

    check_count = 0
    check_mask = 0
    pins: list[Pin] = []
    pin_lookup: dict[int, int] = {}

    def process_attackers(attack_mask: int, candidates: int) -> None:
        nonlocal check_count, check_mask, pins, pin_lookup

        for attacker_square in iterate_bits(attack_mask & candidates):
            ray_mask = INBETWEEN_BITBOARDS[king_square][attacker_square]
            pinned_mask = ray_mask & friendly_occupancies

            if pinned_mask == 0:
                check_mask |= ray_mask
                check_count += 1
                continue

            pinned_square = bitscan_forward(pinned_mask)
            pinned_mask &= pinned_mask - 1

            if pinned_mask == 0:
                pins.append(Pin(pinned_square, attacker_square))
                pin_lookup[pinned_square] = ray_mask

    process_attackers(
        get_bishop_moves_separate(king_square, enemy_occupancies),
        enemy_bishop_bb | enemy_queen_bb,
    )
    process_attackers(
        get_rook_moves_separate(king_square, enemy_occupancies),
        enemy_rook_bb | enemy_queen_bb,
    )

    return check_count, check_mask, pins, pin_lookup


def analyze_king_state(
    piece_array_local: Sequence[int],
    is_white: bool,
    friendly_occupancies: int,
    enemy_occupancies: int,
) -> KingState:
    king_piece = WK if is_white else BK
    enemy_pawn_piece = BP if is_white else WP
    enemy_knight_piece = BN if is_white else WN
    enemy_bishop_piece = BB if is_white else WB
    enemy_rook_piece = BR if is_white else WR
    enemy_queen_piece = BQ if is_white else WQ
    enemy_king_piece = BK if is_white else WK

    pawn_attack_table = WHITE_PAWN_ATTACKS if is_white else BLACK_PAWN_ATTACKS

    king_square = bitscan_forward(piece_array_local[king_piece])
    check_count = 0
    check_mask = 0

    pawn_attackers = piece_array_local[enemy_pawn_piece] & pawn_attack_table[king_square]
    if pawn_attackers != 0:
        check_square = bitscan_forward(pawn_attackers)
        check_mask = SQUARE_BBS[check_square]
        check_count += 1

    knight_attackers = piece_array_local[enemy_knight_piece] & KNIGHT_ATTACKS[king_square]
    if knight_attackers != 0:
        check_square = bitscan_forward(knight_attackers)
        check_mask = SQUARE_BBS[check_square]
        check_count += 1

    king_attackers = piece_array_local[enemy_king_piece] & KING_ATTACKS[king_square]
    if king_attackers != 0:
        check_square = bitscan_forward(king_attackers)
        check_mask = SQUARE_BBS[check_square]
        check_count += 1

    slider_checks, slider_mask, pins, pin_lookup = scan_slider_checks_and_pins(
        king_square,
        piece_array_local[enemy_bishop_piece],
        piece_array_local[enemy_rook_piece],
        piece_array_local[enemy_queen_piece],
        friendly_occupancies,
        enemy_occupancies,
    )

    if slider_checks != 0:
        check_mask = slider_mask
        check_count += slider_checks

    return KingState(king_square, check_count, check_mask, pins, pin_lookup)


def generate_king_moves(
    piece_array_local: Sequence[int],
    king_state: KingState,
    is_white: bool,
    friendly_occupancies: int,
    enemy_occupancies: int,
    combined_occupancies: int,
    empty_occupancies: int,  # noqa: ARG001
    castle_rights: Sequence[bool],
    allow_castle: bool,
) -> list[Move]:
    moves: list[Move] = []

    king_piece = WK if is_white else BK
    enemy_pawn_piece = BP if is_white else WP
    enemy_knight_piece = BN if is_white else WN
    enemy_bishop_piece = BB if is_white else WB
    enemy_rook_piece = BR if is_white else WR
    enemy_queen_piece = BQ if is_white else WQ
    enemy_king_piece = BK if is_white else WK

    pawn_attack_table = WHITE_PAWN_ATTACKS if is_white else BLACK_PAWN_ATTACKS

    king_square = king_state.king_square
    occupancies_without_king = combined_occupancies & (~piece_array_local[king_piece])
    candidate_targets = KING_ATTACKS[king_square] & (~friendly_occupancies & BOARD_MASK)

    for target_square in iterate_bits(candidate_targets):
        target_mask = SQUARE_BBS[target_square]

        if (piece_array_local[enemy_pawn_piece] & pawn_attack_table[target_square]) != 0:
            continue

        if (piece_array_local[enemy_knight_piece] & KNIGHT_ATTACKS[target_square]) != 0:
            continue

        if (piece_array_local[enemy_king_piece] & KING_ATTACKS[target_square]) != 0:
            continue

        bishop_attacks = get_bishop_moves_separate(target_square, occupancies_without_king)
        if (piece_array_local[enemy_bishop_piece] & bishop_attacks) != 0:
            continue

        if (piece_array_local[enemy_queen_piece] & bishop_attacks) != 0:
            continue

        rook_attacks = get_rook_moves_separate(target_square, occupancies_without_king)
        if (piece_array_local[enemy_rook_piece] & rook_attacks) != 0:
            continue

        if (piece_array_local[enemy_queen_piece] & rook_attacks) != 0:
            continue

        tag = TAG_CAPTURE if (enemy_occupancies & target_mask) != 0 else TAG_NONE
        moves.append(Move(king_square, target_square, tag, king_piece))

    if not allow_castle or king_state.check_count != 0:
        return moves

    if is_white and king_square == E1:
        if (
            castle_rights[WKS_CASTLE_RIGHTS]
            and (WKS_EMPTY_BITBOARD & combined_occupancies) == 0
            and (piece_array_local[WR] & SQUARE_BBS[H1]) != 0
            and (not is_square_attacked_by_black(F1, combined_occupancies, piece_array_local))
            and (not is_square_attacked_by_black(G1, combined_occupancies, piece_array_local))
        ):
            moves.append(Move(E1, G1, TAG_WCASTLEKS, WK))

        if (
            castle_rights[WQS_CASTLE_RIGHTS]
            and (WQS_EMPTY_BITBOARD & combined_occupancies) == 0
            and (piece_array_local[WR] & SQUARE_BBS[A1]) != 0
            and (not is_square_attacked_by_black(C1, combined_occupancies, piece_array_local))
            and (not is_square_attacked_by_black(D1, combined_occupancies, piece_array_local))
        ):
            moves.append(Move(E1, C1, TAG_WCASTLEQS, WK))

    if (not is_white) and king_square == E8:
        if (
            castle_rights[BKS_CASTLE_RIGHTS]
            and (BKS_EMPTY_BITBOARD & combined_occupancies) == 0
            and (piece_array_local[BR] & SQUARE_BBS[H8]) != 0
            and (not is_square_attacked_by_white(F8, combined_occupancies, piece_array_local))
            and (not is_square_attacked_by_white(G8, combined_occupancies, piece_array_local))
        ):
            moves.append(Move(E8, G8, TAG_BCASTLEKS, BK))

        if (
            castle_rights[BQS_CASTLE_RIGHTS]
            and (BQS_EMPTY_BITBOARD & combined_occupancies) == 0
            and (piece_array_local[BR] & SQUARE_BBS[A8]) != 0
            and (not is_square_attacked_by_white(C8, combined_occupancies, piece_array_local))
            and (not is_square_attacked_by_white(D8, combined_occupancies, piece_array_local))
        ):
            moves.append(Move(E8, C8, TAG_BCASTLEQS, BK))

    return moves


def generate_leaper_moves(
    piece_bitboard: int,
    attack_table: Sequence[int],
    piece_index: int,
    enemy_occupancies: int,
    empty_occupancies: int,
    check_mask: int,
    pins: Mapping[int, int] | Sequence[Pin],
    king_state: KingState,
) -> list[Move]:
    moves: list[Move] = []
    moves_append = moves.append
    pin_get = pins.get if isinstance(pins, Mapping) else None

    for starting_square in iterate_bits(piece_bitboard):
        allowed_mask = (
            (pin_get(starting_square, MAX_ULONG) if pin_get else pin_mask_for_square(pins, king_state.king_square, starting_square))
            & check_mask
        )
        if allowed_mask == 0:
            continue

        attacks = attack_table[starting_square] & allowed_mask
        capture_targets = attacks & enemy_occupancies
        if capture_targets:
            for target_square in iterate_bits(capture_targets):
                moves_append(Move(starting_square, target_square, TAG_CAPTURE, piece_index))

        quiet_targets = attacks & empty_occupancies
        if quiet_targets:
            for target_square in iterate_bits(quiet_targets):
                moves_append(Move(starting_square, target_square, TAG_NONE, piece_index))

    return moves


def generate_slider_moves(
    piece_bitboard: int,
    attack_fn: Callable[[int, int], int],
    piece_index: int,
    enemy_occupancies: int,
    empty_occupancies: int,
    combined_occupancies: int,
    check_mask: int,
    pins: Mapping[int, int] | Sequence[Pin],
    king_state: KingState,
) -> list[Move]:
    moves: list[Move] = []
    moves_append = moves.append
    pin_get = pins.get if isinstance(pins, Mapping) else None

    for starting_square in iterate_bits(piece_bitboard):
        pin_mask = pin_get(starting_square, MAX_ULONG) if pin_get else pin_mask_for_square(pins, king_state.king_square, starting_square)
        if pin_mask == 0:
            continue

        attack_mask = attack_fn(starting_square, combined_occupancies) & pin_mask & check_mask
        if not attack_mask:
            continue

        capture_targets = attack_mask & enemy_occupancies
        if capture_targets:
            for target_square in iterate_bits(capture_targets):
                moves_append(Move(starting_square, target_square, TAG_CAPTURE, piece_index))

        quiet_targets = attack_mask & empty_occupancies
        if quiet_targets:
            for target_square in iterate_bits(quiet_targets):
                moves_append(Move(starting_square, target_square, TAG_NONE, piece_index))

    return moves


def generate_pawn_moves(
    piece_array_local: Sequence[int],
    is_white: bool,
    enemy_occupancies: int,
    combined_occupancies: int,
    check_mask: int,
    pins: Mapping[int, int] | Sequence[Pin],
    king_state: KingState,
    en_passant_square: int,
) -> list[Move]:
    moves: list[Move] = []
    moves_append = moves.append

    pawn_piece = WP if is_white else BP

    if is_white:
        pawn_bitboard = piece_array_local[WP]
        forward_one_delta = -8
        forward_two_delta = -16
        start_rank_mask = RANK_2_BITBOARD
        promotion_rank_mask = RANK_7_BITBOARD
        ep_rank_mask = RANK_5_BITBOARD
        pawn_attack_table = WHITE_PAWN_ATTACKS
        promotion_tags = (
            TAG_W_QUEEN_PROMOTION,
            TAG_W_ROOK_PROMOTION,
            TAG_W_BISHOP_PROMOTION,
            TAG_W_KNIGHT_PROMOTION,
        )
        capture_promotion_tags = (
            TAG_W_CAPTURE_QUEEN_PROMOTION,
            TAG_W_CAPTURE_ROOK_PROMOTION,
            TAG_W_CAPTURE_BISHOP_PROMOTION,
            TAG_W_CAPTURE_KNIGHT_PROMOTION,
        )
        double_push_tag = TAG_DOUBLE_PAWN_WHITE
        en_passant_tag = TAG_WHITEEP
        captured_pawn_offset = 8
    else:
        pawn_bitboard = piece_array_local[BP]
        forward_one_delta = 8
        forward_two_delta = 16
        start_rank_mask = RANK_7_BITBOARD
        promotion_rank_mask = RANK_2_BITBOARD
        ep_rank_mask = RANK_4_BITBOARD
        pawn_attack_table = BLACK_PAWN_ATTACKS
        promotion_tags = (
            TAG_B_QUEEN_PROMOTION,
            TAG_B_ROOK_PROMOTION,
            TAG_B_BISHOP_PROMOTION,
            TAG_B_KNIGHT_PROMOTION,
        )
        capture_promotion_tags = (
            TAG_B_CAPTURE_QUEEN_PROMOTION,
            TAG_B_CAPTURE_ROOK_PROMOTION,
            TAG_B_CAPTURE_BISHOP_PROMOTION,
            TAG_B_CAPTURE_KNIGHT_PROMOTION,
        )
        double_push_tag = TAG_DOUBLE_PAWN_BLACK
        en_passant_tag = TAG_BLACKEP
        captured_pawn_offset = -8

    pin_get = pins.get if isinstance(pins, Mapping) else None

    for starting_square in iterate_bits(pawn_bitboard):
        pin_mask = pin_get(starting_square, MAX_ULONG) if pin_get else pin_mask_for_square(pins, king_state.king_square, starting_square)
        start_mask = SQUARE_BBS[starting_square]
        allowed_mask = check_mask & pin_mask

        forward_one_square = starting_square + forward_one_delta
        forward_one_mask = SQUARE_BBS[forward_one_square]
        if (forward_one_mask & combined_occupancies) == 0:
            if (start_mask & promotion_rank_mask) != 0:
                if (forward_one_mask & allowed_mask) != 0:
                    for tag in promotion_tags:
                        moves_append(Move(starting_square, forward_one_square, tag, pawn_piece))
            else:
                if (forward_one_mask & allowed_mask) != 0:
                    moves_append(Move(starting_square, forward_one_square, TAG_NONE, pawn_piece))

                if (start_mask & start_rank_mask) != 0:
                    forward_two_square = starting_square + forward_two_delta
                    forward_two_mask = SQUARE_BBS[forward_two_square]
                    if (
                        (forward_two_mask & combined_occupancies) == 0
                        and (forward_two_mask & allowed_mask) != 0
                    ):
                        moves_append(Move(starting_square, forward_two_square, double_push_tag, pawn_piece))

        capture_targets = (pawn_attack_table[starting_square] & enemy_occupancies) & allowed_mask
        if capture_targets:
            for target_square in iterate_bits(capture_targets):
                if (start_mask & promotion_rank_mask) != 0:
                    for tag in capture_promotion_tags:
                        moves_append(Move(starting_square, target_square, tag, pawn_piece))
                else:
                    moves_append(Move(starting_square, target_square, TAG_CAPTURE, pawn_piece))

        if (
            en_passant_square != NO_SQUARE
            and (start_mask & ep_rank_mask) != 0
            and (pawn_attack_table[starting_square] & SQUARE_BBS[en_passant_square]) != 0
            and (SQUARE_BBS[en_passant_square] & allowed_mask) != 0
        ):
            king_rank_mask = RANK_5_BITBOARD if is_white else RANK_4_BITBOARD
            enemy_rook_piece = BR if is_white else WR
            enemy_queen_piece = BQ if is_white else WQ
            king_piece = WK if is_white else BK

            if (piece_array_local[king_piece] & king_rank_mask) == 0 or (
                (piece_array_local[enemy_rook_piece] & king_rank_mask) == 0
                and (piece_array_local[enemy_queen_piece] & king_rank_mask) == 0
            ):
                moves_append(Move(starting_square, en_passant_square, en_passant_tag, pawn_piece))
            else:
                occupancy_without_ep = combined_occupancies & ~SQUARE_BBS[starting_square]
                occupancy_without_ep &= ~SQUARE_BBS[en_passant_square + captured_pawn_offset]

                rook_attacks_from_king = get_rook_moves_separate(
                    king_state.king_square,
                    occupancy_without_ep,
                )

                if (rook_attacks_from_king & piece_array_local[enemy_rook_piece]) == 0 and (
                    rook_attacks_from_king & piece_array_local[enemy_queen_piece]
                ) == 0:
                    moves_append(Move(starting_square, en_passant_square, en_passant_tag, pawn_piece))

    return moves


def generate_moves_for_side(
    piece_array_local: Sequence[int],
    white_to_move: bool,
    castle_rights: Sequence[bool],
    en_passant_square: int,
    white_occupancies: int,
    black_occupancies: int,
    combined_occupancies: int,
) -> list[Move]:
    empty_occupancies = (~combined_occupancies) & BOARD_MASK

    if white_to_move:
        friendly_occ = white_occupancies
        enemy_occ = black_occupancies
    else:
        friendly_occ = black_occupancies
        enemy_occ = white_occupancies

    king_state = analyze_king_state(piece_array_local, white_to_move, friendly_occ, enemy_occ)

    if king_state.check_count > 1:
        return generate_king_moves(
            piece_array_local,
            king_state,
            white_to_move,
            friendly_occ,
            enemy_occ,
            combined_occupancies,
            empty_occupancies,
            castle_rights,
            allow_castle=False,
        )

    check_mask = king_state.check_mask if king_state.check_count == 1 else MAX_ULONG

    moves: list[Move] = []
    moves.extend(
        generate_king_moves(
            piece_array_local,
            king_state,
            white_to_move,
            friendly_occ,
            enemy_occ,
            combined_occupancies,
            empty_occupancies,
            castle_rights,
            allow_castle=king_state.check_count == 0,
        )
    )

    knight_piece = WN if white_to_move else BN
    moves.extend(
        generate_leaper_moves(
            piece_array_local[knight_piece],
            KNIGHT_ATTACKS,
            knight_piece,
            enemy_occ,
            empty_occupancies,
            check_mask,
            king_state.pin_lookup,
            king_state,
        )
    )

    moves.extend(
        generate_pawn_moves(
            piece_array_local,
            white_to_move,
            enemy_occ,
            combined_occupancies,
            check_mask,
            king_state.pin_lookup,
            king_state,
            en_passant_square,
        )
    )

    bishop_piece = WB if white_to_move else BB
    moves.extend(
        generate_slider_moves(
            piece_array_local[bishop_piece],
            get_bishop_moves_separate,
            bishop_piece,
            enemy_occ,
            empty_occupancies,
            combined_occupancies,
            check_mask,
            king_state.pin_lookup,
            king_state,
        )
    )

    rook_piece = WR if white_to_move else BR
    moves.extend(
        generate_slider_moves(
            piece_array_local[rook_piece],
            get_rook_moves_separate,
            rook_piece,
            enemy_occ,
            empty_occupancies,
            combined_occupancies,
            check_mask,
            king_state.pin_lookup,
            king_state,
        )
    )

    queen_piece = WQ if white_to_move else BQ

    def queen_attack_fn(square: int, occupancies: int) -> int:
        return get_rook_moves_separate(square, occupancies) | get_bishop_moves_separate(square, occupancies)

    moves.extend(
        generate_slider_moves(
            piece_array_local[queen_piece],
            queen_attack_fn,
            queen_piece,
            enemy_occ,
            empty_occupancies,
            combined_occupancies,
            check_mask,
            king_state.pin_lookup,
            king_state,
        )
    )

    return moves


def apply_move(move: Move) -> MoveContext:
    global white_to_play
    global ep

    previous_ep = ep
    previous_castle = (
        castle_rights[0],
        castle_rights[1],
        castle_rights[2],
        castle_rights[3],
    )
    capture_index = -1

    white_to_play = not white_to_play

    piece_arr = piece_array
    castle = castle_rights
    start_mask = 1 << move.starting
    target_mask = 1 << move.target
    tag = move.tag

    def add(piece_index: int, mask: int) -> None:
        piece_arr[piece_index] |= mask

    def remove(piece_index: int, mask: int) -> None:
        piece_arr[piece_index] &= ~mask

    ep = NO_SQUARE

    if tag in (TAG_NONE, TAG_CHECK):
        add(move.piece, target_mask)
        remove(move.piece, start_mask)
    elif tag in (TAG_CAPTURE, TAG_CHECK_CAPTURE):
        add(move.piece, target_mask)
        remove(move.piece, start_mask)
        capture_index = locate_captured_piece(move.target, move.piece)
        if capture_index != -1:
            remove(capture_index, target_mask)
    elif tag == TAG_WHITEEP:
        add(move.piece, target_mask)
        remove(move.piece, start_mask)
        remove(BP, SQUARE_BBS[move.target + 8])
        capture_index = BP
    elif tag == TAG_BLACKEP:
        add(move.piece, target_mask)
        remove(move.piece, start_mask)
        remove(WP, SQUARE_BBS[move.target - 8])
        capture_index = WP
    elif tag == TAG_WCASTLEKS:
        add(WK, SQUARE_BBS[G1])
        remove(WK, SQUARE_BBS[E1])
        add(WR, SQUARE_BBS[F1])
        remove(WR, SQUARE_BBS[H1])
    elif tag == TAG_WCASTLEQS:
        add(WK, SQUARE_BBS[C1])
        remove(WK, SQUARE_BBS[E1])
        add(WR, SQUARE_BBS[D1])
        remove(WR, SQUARE_BBS[A1])
    elif tag == TAG_BCASTLEKS:
        add(BK, SQUARE_BBS[G8])
        remove(BK, SQUARE_BBS[E8])
        add(BR, SQUARE_BBS[F8])
        remove(BR, SQUARE_BBS[H8])
    elif tag == TAG_BCASTLEQS:
        add(BK, SQUARE_BBS[C8])
        remove(BK, SQUARE_BBS[E8])
        add(BR, SQUARE_BBS[D8])
        remove(BR, SQUARE_BBS[A8])
    elif tag in PROMOTION_MAP:
        promoted_piece = PROMOTION_MAP[tag]
        add(promoted_piece, target_mask)
        remove(move.piece, start_mask)
    elif tag in CAPTURE_PROMOTION_MAP:
        promoted_piece = CAPTURE_PROMOTION_MAP[tag]
        add(promoted_piece, target_mask)
        remove(move.piece, start_mask)
        capture_index = locate_captured_piece(move.target, move.piece)
        if capture_index != -1:
            remove(capture_index, target_mask)
    elif tag == TAG_DOUBLE_PAWN_WHITE:
        add(move.piece, target_mask)
        remove(move.piece, start_mask)
        ep = move.target + 8
    elif tag == TAG_DOUBLE_PAWN_BLACK:
        add(move.piece, target_mask)
        remove(move.piece, start_mask)
        ep = move.target - 8
    else:
        msg = f"Unsupported move tag {move.tag}"
        raise ValueError(msg)

    if move.piece == WK:
        castle[WKS_CASTLE_RIGHTS] = False
        castle[WQS_CASTLE_RIGHTS] = False
    elif move.piece == BK:
        castle[BKS_CASTLE_RIGHTS] = False
        castle[BQS_CASTLE_RIGHTS] = False
    elif move.piece == WR:
        if castle[WKS_CASTLE_RIGHTS] and (piece_arr[WR] & SQUARE_BBS[H1]) == 0:
            castle[WKS_CASTLE_RIGHTS] = False
        if castle[WQS_CASTLE_RIGHTS] and (piece_arr[WR] & SQUARE_BBS[A1]) == 0:
            castle[WQS_CASTLE_RIGHTS] = False
    elif move.piece == BR:
        if castle[BKS_CASTLE_RIGHTS] and (piece_arr[BR] & SQUARE_BBS[H8]) == 0:
            castle[BKS_CASTLE_RIGHTS] = False
        if castle[BQS_CASTLE_RIGHTS] and (piece_arr[BR] & SQUARE_BBS[A8]) == 0:
            castle[BQS_CASTLE_RIGHTS] = False

    return MoveContext(capture_index, previous_ep, previous_castle)


def undo_move(move: Move, context: MoveContext) -> None:
    global white_to_play
    global ep

    white_to_play = not white_to_play

    piece_arr = piece_array
    start_mask = 1 << move.starting
    target_mask = 1 << move.target
    tag = move.tag

    def add(piece_index: int, mask: int) -> None:
        piece_arr[piece_index] |= mask

    def remove(piece_index: int, mask: int) -> None:
        piece_arr[piece_index] &= ~mask

    if tag in (TAG_NONE, TAG_CHECK):
        add(move.piece, start_mask)
        remove(move.piece, target_mask)
    elif tag in (TAG_CAPTURE, TAG_CHECK_CAPTURE):
        add(move.piece, start_mask)
        remove(move.piece, target_mask)
        if context.captured_piece_index != -1:
            add(context.captured_piece_index, target_mask)
    elif tag == TAG_WHITEEP:
        add(move.piece, start_mask)
        remove(move.piece, target_mask)
        add(BP, SQUARE_BBS[move.target + 8])
    elif tag == TAG_BLACKEP:
        add(move.piece, start_mask)
        remove(move.piece, target_mask)
        add(WP, SQUARE_BBS[move.target - 8])
    elif tag == TAG_WCASTLEKS:
        add(WK, SQUARE_BBS[E1])
        remove(WK, SQUARE_BBS[G1])
        add(WR, SQUARE_BBS[H1])
        remove(WR, SQUARE_BBS[F1])
    elif tag == TAG_WCASTLEQS:
        add(WK, SQUARE_BBS[E1])
        remove(WK, SQUARE_BBS[C1])
        add(WR, SQUARE_BBS[A1])
        remove(WR, SQUARE_BBS[D1])
    elif tag == TAG_BCASTLEKS:
        add(BK, SQUARE_BBS[E8])
        remove(BK, SQUARE_BBS[G8])
        add(BR, SQUARE_BBS[H8])
        remove(BR, SQUARE_BBS[F8])
    elif tag == TAG_BCASTLEQS:
        add(BK, SQUARE_BBS[E8])
        remove(BK, SQUARE_BBS[C8])
        add(BR, SQUARE_BBS[A8])
        remove(BR, SQUARE_BBS[D8])
    elif tag in PROMOTION_MAP:
        promoted_piece = PROMOTION_MAP[tag]
        add(move.piece, start_mask)
        remove(promoted_piece, target_mask)
    elif tag in CAPTURE_PROMOTION_MAP:
        promoted_piece = CAPTURE_PROMOTION_MAP[tag]
        add(move.piece, start_mask)
        remove(promoted_piece, target_mask)
        if context.captured_piece_index != -1:
            add(context.captured_piece_index, target_mask)
    elif tag in (TAG_DOUBLE_PAWN_WHITE, TAG_DOUBLE_PAWN_BLACK):
        add(move.piece, start_mask)
        remove(move.piece, target_mask)
    else:
        msg = f"Unsupported move tag {move.tag}"
        raise ValueError(msg)

    castle_rights[0], castle_rights[1], castle_rights[2], castle_rights[3] = context.previous_castle_rights
    ep = context.previous_ep


def print_move_no_nl(starting: int, target_square: int, tag: int):  # starting
    if starting < 0 or starting > 63:
        print(f"{starting}", end="")
    else:
        print(f"{SQ_CHAR_X[starting]}", end="")
        print(f"{SQ_CHAR_Y[starting]}", end="")

    # target
    if target_square < 0 or target_square > 63:
        print("%d", target_square)
    else:
        print(f"{SQ_CHAR_X[target_square]}", end="")
        print(f"{SQ_CHAR_Y[target_square]}", end="")

    if tag in (
        TAG_B_CAPTURE_KNIGHT_PROMOTION,
        TAG_B_KNIGHT_PROMOTION,
        TAG_W_KNIGHT_PROMOTION,
        TAG_W_CAPTURE_KNIGHT_PROMOTION,
    ):
        print("n", end="")
    elif tag in (
        TAG_B_CAPTURE_ROOK_PROMOTION,
        TAG_B_ROOK_PROMOTION,
        TAG_W_ROOK_PROMOTION,
        TAG_W_CAPTURE_ROOK_PROMOTION,
    ):
        print("r", end="")
    elif tag in (
        TAG_B_CAPTURE_BISHOP_PROMOTION,
        TAG_B_BISHOP_PROMOTION,
        TAG_W_BISHOP_PROMOTION,
        TAG_W_CAPTURE_BISHOP_PROMOTION,
    ):
        print("b", end="")
    elif tag in (
        TAG_B_CAPTURE_QUEEN_PROMOTION,
        TAG_B_QUEEN_PROMOTION,
        TAG_W_QUEEN_PROMOTION,
        TAG_W_CAPTURE_QUEEN_PROMOTION,
    ):
        pass


def get_rook_moves_separate(square: int, combined_occ: int) -> int:
    combined_attacks = 0

    rook_attack_up: int = ROOK_ATTACKS[ROOK_UP][square]
    rook_and_occs = rook_attack_up & combined_occ
    if rook_and_occs != 0:
        last_value = rook_and_occs
        for _i in range(8):
            rook_and_occs = rook_and_occs & rook_and_occs - 1
            if rook_and_occs == 0:
                end_square: int = bitscan_forward(last_value)
                combined_attacks |= INBETWEEN_BITBOARDS[square][end_square]
                break
            last_value = rook_and_occs
    else:
        combined_attacks |= rook_attack_up

    rook_attack_left = ROOK_ATTACKS[ROOK_LEFT][square]
    rook_and_occs = rook_attack_left & combined_occ
    if rook_and_occs != 0:
        last_value = rook_and_occs
        for _i in range(8):
            rook_and_occs = rook_and_occs & rook_and_occs - 1
            if rook_and_occs == 0:
                end_square: int = bitscan_forward(last_value)
                combined_attacks |= INBETWEEN_BITBOARDS[square][end_square]
                break
            last_value = rook_and_occs
    else:
        combined_attacks |= rook_attack_left

    rook_attack_down = ROOK_ATTACKS[ROOK_DOWN][square]
    rook_and_occs = rook_attack_down & combined_occ

    if rook_and_occs != 0:
        end_square = bitscan_forward(rook_and_occs)
        combined_attacks |= INBETWEEN_BITBOARDS[square][end_square]
    else:
        combined_attacks |= rook_attack_down

    rook_attack_right = ROOK_ATTACKS[ROOK_RIGHT][square]
    rook_and_occs = rook_attack_right & combined_occ

    if rook_and_occs != 0:
        end_square = bitscan_forward(rook_and_occs)
        combined_attacks |= INBETWEEN_BITBOARDS[square][end_square]
    else:
        combined_attacks |= rook_attack_right

    return combined_attacks


def get_bishop_moves_separate(square, combined_occ):
    combined_attacks = 0
    bishop_attack_up_left = BISHOP_ATTACKS[BISHOP_UP_LEFT][square]
    bishop_and_occs = bishop_attack_up_left & combined_occ
    if bishop_and_occs != 0:
        last_value = bishop_and_occs
        for _i in range(8):
            bishop_and_occs &= bishop_and_occs - 1
            if bishop_and_occs == 0:
                end_square = bitscan_forward(last_value)
                combined_attacks |= INBETWEEN_BITBOARDS[square][end_square]
                break
            last_value = bishop_and_occs
    else:
        combined_attacks |= bishop_attack_up_left

    bishop_attack_up_right = BISHOP_ATTACKS[BISHOP_UP_RIGHT][square]
    bishop_and_occs = bishop_attack_up_right & combined_occ
    if bishop_and_occs != 0:
        last_value = bishop_and_occs
        for _i in range(8):
            bishop_and_occs &= bishop_and_occs - 1
            if bishop_and_occs == 0:
                end_square: int = bitscan_forward(last_value)
                combined_attacks |= INBETWEEN_BITBOARDS[square][end_square]
                break

            last_value = bishop_and_occs
    else:
        combined_attacks |= bishop_attack_up_right

    bishop_attack_down_left = BISHOP_ATTACKS[BISHOP_DOWN_LEFT][square]
    bishop_and_occs = bishop_attack_down_left & combined_occ

    if bishop_and_occs != 0:
        end_square = bitscan_forward(bishop_and_occs)
        combined_attacks |= INBETWEEN_BITBOARDS[square][end_square]
    else:
        combined_attacks |= bishop_attack_down_left

    bishop_attack_down_right = BISHOP_ATTACKS[BISHOP_DOWN_RIGHT][square]
    bishop_and_occs = bishop_attack_down_right & combined_occ
    if bishop_and_occs != 0:
        end_square = bitscan_forward(bishop_and_occs)
        combined_attacks |= INBETWEEN_BITBOARDS[square][end_square]
    else:
        combined_attacks |= bishop_attack_down_right

    return combined_attacks


def is_square_attacked_by_black(
    square: int,
    occupancy: int,
    pieces: Sequence[int] | None = None,
) -> bool:
    pieces = piece_array if pieces is None else pieces

    if (pieces[BP] & WHITE_PAWN_ATTACKS[square]) != 0:
        return True

    if (pieces[BN] & KNIGHT_ATTACKS[square]) != 0:
        return True

    if (pieces[BK] & KING_ATTACKS[square]) != 0:
        return True

    bishop_attacks: int = get_bishop_moves_separate(square, occupancy)
    if (pieces[BB] & bishop_attacks) != 0:
        return True

    if (pieces[BQ] & bishop_attacks) != 0:
        return True

    rook_attacks: int = get_rook_moves_separate(square, occupancy)
    if (pieces[BR] & rook_attacks) != 0:
        return True

    return (pieces[BQ] & rook_attacks) != 0


def is_square_attacked_by_white(
    square: int,
    occupancy: int,
    pieces: Sequence[int] | None = None,
) -> bool:
    pieces = piece_array if pieces is None else pieces

    if (pieces[WP] & BLACK_PAWN_ATTACKS[square]) != 0:
        return True

    if (pieces[WN] & KNIGHT_ATTACKS[square]) != 0:
        return True

    if (pieces[WK] & KING_ATTACKS[square]) != 0:
        return True

    bishop_attacks: int = get_bishop_moves_separate(square, occupancy)
    if (pieces[WB] & bishop_attacks) != 0:
        return True

    if (pieces[WQ] & bishop_attacks) != 0:
        return True

    rook_attacks: int = get_rook_moves_separate(square, occupancy)
    if (pieces[WR] & rook_attacks) != 0:
        return True

    return (pieces[WQ] & rook_attacks) != 0


# fmt: off
MAGIC: int = 0x03F79D71B4CB0A89
DEBRUIJN64: list[int] = [
    0, 47, 1, 56, 48, 27, 2, 60,
    57, 49, 41, 37, 28, 16, 3, 61,
    54, 58, 35, 52, 50, 42, 21, 44,
    38, 32, 29, 23, 17, 11, 4, 62,
    46, 55, 26, 59, 40, 36, 15, 53,
    34, 51, 20, 43, 31, 22, 10, 45,
    25, 39, 14, 33, 19, 30, 9, 24,
    13, 18, 8, 12, 7, 6, 5, 63,
]
# fmt: on


def bitscan_forward(temp_bitboard: int) -> int:
    lsb = temp_bitboard & -temp_bitboard
    return (lsb.bit_length() - 1) if lsb else -1


def set_starting_position():
    global ep
    global white_to_play
    ep = NO_SQUARE
    white_to_play = True
    castle_rights[0] = True
    castle_rights[1] = True
    castle_rights[2] = True
    castle_rights[3] = True
    piece_array[WP] = WP_STARTING_POSITIONS
    piece_array[WN] = WN_STARTING_POSITIONS
    piece_array[WB] = WB_STARTING_POSITIONS
    piece_array[WR] = WR_STARTING_POSITIONS
    piece_array[WQ] = WQ_STARTING_POSITION
    piece_array[WK] = WK_STARTING_POSITION
    piece_array[BP] = BP_STARTING_POSITIONS
    piece_array[BN] = BN_STARTING_POSITIONS
    piece_array[BB] = BB_STARTING_POSITIONS
    piece_array[BR] = BR_STARTING_POSITIONS
    piece_array[BQ] = BQ_STARTING_POSITION
    piece_array[BK] = BK_STARTING_POSITION


class Board:
    __slots__ = ("castle_rights", "ep", "piece_array", "white_to_play")

    def __init__(self):
        # Corresponds to piece_array
        self.piece_array = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        # Corresponds to is_white
        self.white_to_play = True
        # Corresponds to castle_rights
        self.castle_rights = [True, True, True, True]
        self.ep = NO_SQUARE


def set_starting_position_struct(board: Board):
    board.ep = NO_SQUARE
    board.white_to_play = True
    board.castle_rights[0] = True
    board.castle_rights[1] = True
    board.castle_rights[2] = True
    board.castle_rights[3] = True
    board.piece_array[WP] = WP_STARTING_POSITIONS
    board.piece_array[WN] = WN_STARTING_POSITIONS
    board.piece_array[WB] = WB_STARTING_POSITIONS
    board.piece_array[WR] = WR_STARTING_POSITIONS
    board.piece_array[WQ] = WQ_STARTING_POSITION
    board.piece_array[WK] = WK_STARTING_POSITION
    board.piece_array[BP] = BP_STARTING_POSITIONS
    board.piece_array[BN] = BN_STARTING_POSITIONS
    board.piece_array[BB] = BB_STARTING_POSITIONS
    board.piece_array[BR] = BR_STARTING_POSITIONS
    board.piece_array[BQ] = BQ_STARTING_POSITION
    board.piece_array[BK] = BK_STARTING_POSITION


def is_occupied(bitboard: int, square: int) -> bool:
    return (bitboard & SQUARE_BBS[square]) != 0


def get_occupied_index(square: int) -> int:
    for i in range(12):
        if is_occupied(piece_array[i], square):
            return i

    return EMPTY


def print_board():
    print("Board:")
    board_array = [0] * 64

    for i in range(64):
        board_array[i] = get_occupied_index(i)

    for rank in range(8):
        print("   ", end="")
        for file in range(8):
            square: int = (rank * 8) + file
            print(f"{piece_colours[board_array[square]]}{piece_names[board_array[square]]} ", end="")
        print()
    print()

    print(f"White to play: {white_to_play}")

    print(f"Castle: {castle_rights[0]} {castle_rights[1]} {castle_rights[2]} {castle_rights[3]}")
    print(f"ep: {ep}")
    print(f"ply: {board_ply}")
    print()
    print()


def perft_inline(depth: int, ply: int) -> int:
    global white_to_play
    global ep

    white_occupancies: int = (
        piece_array[WP]
        | piece_array[WN]
        | piece_array[WB]
        | piece_array[WR]
        | piece_array[WQ]
        | piece_array[WK]
    )
    black_occupancies: int = (
        piece_array[BP]
        | piece_array[BN]
        | piece_array[BB]
        | piece_array[BR]
        | piece_array[BQ]
        | piece_array[BK]
    )

    combined_occupancies: int = white_occupancies | black_occupancies

    move_list = generate_moves_for_side(
        piece_array,
        white_to_play,
        castle_rights,
        ep,
        white_occupancies,
        black_occupancies,
        combined_occupancies,
    )

    if depth == 1:
        return len(move_list)

    nodes: int = 0

    for move in move_list:
        move_context = apply_move(move)
        prior_nodes = nodes
        nodes += perft_inline(depth - 1, ply + 1)
        undo_move(move, move_context)

        if ply == 0:
            print_move_no_nl(move.starting, move.target, move.tag)
            print(f": {nodes - prior_nodes}")

    return nodes


def run_perft_inline(depth: int):
    timestamp_start = time.monotonic_ns()

    nodes: int = perft_inline(depth, 0)

    timestamp_end = time.monotonic_ns()
    elapsed = timestamp_end - timestamp_start

    print(f"Nodes: {nodes}")
    print(f"Elapsed time: {elapsed / 1_000_000} ms")


if __name__ == "__main__":
    set_starting_position()
    print_board()

    run_perft_inline(6)
    # run_perft_inline_struct(6) # noqa: ERA001
