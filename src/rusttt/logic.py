import time

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
    EMPTY_BITBOARD,
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
    MOVE_PIECE,
    MOVE_STARTING,
    MOVE_TAG,
    MOVE_TARGET,
    NO_SQUARE,
    PINNED_SQUARE_INDEX,
    PINNING_PIECE_INDEX,
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


def is_square_attacked_by_black(square: int, occupancy: int) -> bool:
    if (piece_array[BP] & WHITE_PAWN_ATTACKS[square]) != 0:
        return True

    if (piece_array[BN] & KNIGHT_ATTACKS[square]) != 0:
        return True

    if (piece_array[BK] & KING_ATTACKS[square]) != 0:
        return True

    bishop_attacks: int = get_bishop_moves_separate(square, occupancy)
    if (piece_array[BB] & bishop_attacks) != 0:
        return True

    if (piece_array[BQ] & bishop_attacks) != 0:
        return True

    rook_attacks: int = get_rook_moves_separate(square, occupancy)
    if (piece_array[BR] & rook_attacks) != 0:
        return True

    return piece_array[BQ] & rook_attacks != 0


def is_square_attacked_by_white(square: int, occupancy: int) -> bool:
    if (piece_array[WP] & BLACK_PAWN_ATTACKS[square]) != 0:
        return True

    if (piece_array[WN] & KNIGHT_ATTACKS[square]) != 0:
        return True

    if (piece_array[WK] & KING_ATTACKS[square]) != 0:
        return True

    bishop_attacks: int = get_bishop_moves_separate(square, occupancy)
    if (piece_array[WB] & bishop_attacks) != 0:
        return True

    if (piece_array[WQ] & bishop_attacks) != 0:
        return True

    rook_attacks: int = get_rook_moves_separate(square, occupancy)
    if (piece_array[WR] & rook_attacks) != 0:
        return True

    return piece_array[WQ] & rook_attacks != 0


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
    result = MAGIC * (temp_bitboard ^ (temp_bitboard - 1))
    index = (result & ((1 << 64) - 1)) >> 58
    if index < 0 or index > 63:
        print(f"error {index} out of range")
        return -1

    return DEBRUIJN64[index]


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

    piece_array_local = [
        piece_array[0],
        piece_array[1],
        piece_array[2],
        piece_array[3],
        piece_array[4],
        piece_array[5],
        piece_array[6],
        piece_array[7],
        piece_array[8],
        piece_array[9],
        piece_array[10],
        piece_array[11],
    ]

    # if depth == 0:
    #    return 1  # noqa: ERA001

    move_list = [[0] * 4 for _ in range(50)]
    move_count: int = 0

    white_occupancies: int = (
        piece_array_local[0]
        | piece_array_local[1]
        | piece_array_local[2]
        | piece_array_local[3]
        | piece_array_local[4]
        | piece_array_local[5]
    )
    black_occupancies: int = (
        piece_array_local[6]
        | piece_array_local[7]
        | piece_array_local[8]
        | piece_array_local[9]
        | piece_array_local[10]
        | piece_array_local[11]
    )

    combined_occupancies: int = white_occupancies | black_occupancies
    empty_occupancies: int = ~combined_occupancies
    temp_bitboard: int
    check_bitboard: int = 0
    temp_pin_bitboard: int
    temp_attack: int
    temp_empty: int
    temp_captures: int
    starting_square: int = NO_SQUARE
    target_square: int = NO_SQUARE

    pin_array = [[-1, -1] for _ in range(8)]
    pin_number: int = 0

    # Generate Moves
    if white_to_play:
        white_king_check_count: int = 0
        white_king_position: int = bitscan_forward(piece_array_local[WK])

        # pawns
        temp_bitboard = piece_array_local[BP] & WHITE_PAWN_ATTACKS[white_king_position]
        if temp_bitboard != 0:
            pawn_square: int = bitscan_forward(temp_bitboard)
            check_bitboard = EMPTY_BITBOARD << pawn_square
            white_king_check_count += 1

        # knights
        temp_bitboard = piece_array_local[BN] & KNIGHT_ATTACKS[white_king_position]
        if temp_bitboard != 0:
            knight_square: int = bitscan_forward(temp_bitboard)
            check_bitboard = SQUARE_BBS[knight_square]
            white_king_check_count += 1

        # bishops
        bishop_attacks_checks: int = get_bishop_moves_separate(white_king_position, black_occupancies)
        temp_bitboard = piece_array_local[BB] & bishop_attacks_checks
        while temp_bitboard != 0:
            piece_square: int = bitscan_forward(temp_bitboard)
            temp_pin_bitboard = INBETWEEN_BITBOARDS[white_king_position][piece_square] & white_occupancies

            if temp_pin_bitboard == 0:
                check_bitboard = INBETWEEN_BITBOARDS[white_king_position][piece_square]
                white_king_check_count += 1
            else:
                pinned_square: int = bitscan_forward(temp_pin_bitboard)
                temp_pin_bitboard &= temp_pin_bitboard - 1

                if temp_pin_bitboard == 0:
                    pin_array[pin_number][PINNED_SQUARE_INDEX] = pinned_square
                    pin_array[pin_number][PINNING_PIECE_INDEX] = piece_square
                    pin_number += 1
            temp_bitboard &= temp_bitboard - 1

        # queen
        temp_bitboard = piece_array_local[BQ] & bishop_attacks_checks
        while temp_bitboard != 0:
            piece_square: int = bitscan_forward(temp_bitboard)
            temp_pin_bitboard = INBETWEEN_BITBOARDS[white_king_position][piece_square] & white_occupancies

            if temp_pin_bitboard == 0:
                check_bitboard = INBETWEEN_BITBOARDS[white_king_position][piece_square]
                white_king_check_count += 1
            else:
                pinned_square: int = bitscan_forward(temp_pin_bitboard)
                temp_pin_bitboard &= temp_pin_bitboard - 1

                if temp_pin_bitboard == 0:
                    pin_array[pin_number][PINNED_SQUARE_INDEX] = pinned_square
                    pin_array[pin_number][PINNING_PIECE_INDEX] = piece_square
                    pin_number += 1

            temp_bitboard &= temp_bitboard - 1

        # rook
        rook_attacks: int = get_rook_moves_separate(white_king_position, black_occupancies)
        temp_bitboard = piece_array_local[BR] & rook_attacks
        while temp_bitboard != 0:
            piece_square: int = bitscan_forward(temp_bitboard)
            temp_pin_bitboard = INBETWEEN_BITBOARDS[white_king_position][piece_square] & white_occupancies
            if temp_pin_bitboard == 0:
                check_bitboard = INBETWEEN_BITBOARDS[white_king_position][piece_square]
                white_king_check_count += 1
            else:
                pinned_square: int = bitscan_forward(temp_pin_bitboard)
                temp_pin_bitboard &= temp_pin_bitboard - 1
                if temp_pin_bitboard == 0:
                    pin_array[pin_number][PINNED_SQUARE_INDEX] = pinned_square
                    pin_array[pin_number][PINNING_PIECE_INDEX] = piece_square
                    pin_number += 1
            temp_bitboard &= temp_bitboard - 1

        # queen
        temp_bitboard = piece_array_local[BQ] & rook_attacks

        while temp_bitboard != 0:
            piece_square: int = bitscan_forward(temp_bitboard)
            temp_pin_bitboard = INBETWEEN_BITBOARDS[white_king_position][piece_square] & white_occupancies

            if temp_pin_bitboard == 0:
                check_bitboard = INBETWEEN_BITBOARDS[white_king_position][piece_square]
                white_king_check_count += 1
            else:
                pinned_square: int = bitscan_forward(temp_pin_bitboard)
                temp_pin_bitboard &= temp_pin_bitboard - 1

                if temp_pin_bitboard == 0:
                    pin_array[pin_number][PINNED_SQUARE_INDEX] = pinned_square
                    pin_array[pin_number][PINNING_PIECE_INDEX] = piece_square
                    pin_number += 1
            temp_bitboard &= temp_bitboard - 1

        # If double check
        if white_king_check_count > 1:
            occupancies_without_white_king: int = combined_occupancies & (~piece_array_local[WK])
            temp_attack = KING_ATTACKS[white_king_position]
            temp_empty = temp_attack & empty_occupancies
            while temp_empty != 0:
                target_square = bitscan_forward(temp_empty)
                temp_empty &= temp_empty - 1

                if (piece_array_local[BP] & WHITE_PAWN_ATTACKS[target_square]) != 0:
                    continue

                if (piece_array_local[BN] & KNIGHT_ATTACKS[target_square]) != 0:
                    continue

                if (piece_array_local[BK] & KING_ATTACKS[target_square]) != 0:
                    continue

                bishop_attacks: int = get_bishop_moves_separate(target_square, occupancies_without_white_king)
                if (piece_array_local[BB] & bishop_attacks) != 0:
                    continue

                if (piece_array_local[BQ] & bishop_attacks) != 0:
                    continue

                rook_attacks: int = get_rook_moves_separate(target_square, occupancies_without_white_king)
                if (piece_array_local[BR] & rook_attacks) != 0:
                    continue

                if (piece_array_local[BQ] & rook_attacks) != 0:
                    continue

                move_list[move_count][MOVE_STARTING] = white_king_position
                move_list[move_count][MOVE_TARGET] = target_square
                move_list[move_count][MOVE_TAG] = TAG_NONE
                move_list[move_count][MOVE_PIECE] = WK
                move_count += 1

            # captures
            temp_captures = temp_attack & black_occupancies
            while temp_captures != 0:
                target_square = bitscan_forward(temp_captures)
                temp_captures &= temp_captures - 1

                if (piece_array_local[BP] & WHITE_PAWN_ATTACKS[target_square]) != 0:
                    continue

                if (piece_array_local[BN] & KNIGHT_ATTACKS[target_square]) != 0:
                    continue

                if (piece_array_local[BK] & KING_ATTACKS[target_square]) != 0:
                    continue

                bishop_attacks: int = get_bishop_moves_separate(target_square, occupancies_without_white_king)
                if (piece_array_local[BB] & bishop_attacks) != 0:
                    continue

                if (piece_array_local[BQ] & bishop_attacks) != 0:
                    continue

                rook_attacks: int = get_rook_moves_separate(target_square, occupancies_without_white_king)
                if (piece_array_local[BR] & rook_attacks) != 0:
                    continue

                if (piece_array_local[BQ] & rook_attacks) != 0:
                    continue

                move_list[move_count][MOVE_STARTING] = white_king_position
                move_list[move_count][MOVE_TARGET] = target_square
                move_list[move_count][MOVE_TAG] = TAG_CAPTURE
                move_list[move_count][MOVE_PIECE] = WK
                move_count += 1
        else:
            if white_king_check_count == 0:
                check_bitboard = MAX_ULONG

            occupancies_without_white_king: int = combined_occupancies & (~piece_array_local[WK])
            temp_attack = KING_ATTACKS[white_king_position]
            temp_empty = temp_attack & empty_occupancies
            while temp_empty != 0:
                target_square = bitscan_forward(temp_empty)
                temp_empty &= temp_empty - 1

                if (piece_array_local[BP] & WHITE_PAWN_ATTACKS[target_square]) != 0:
                    continue

                if (piece_array_local[BN] & KNIGHT_ATTACKS[target_square]) != 0:
                    continue

                if (piece_array_local[BK] & KING_ATTACKS[target_square]) != 0:
                    continue

                bishop_attacks: int = get_bishop_moves_separate(target_square, occupancies_without_white_king)
                if (piece_array_local[BB] & bishop_attacks) != 0:
                    continue

                if (piece_array_local[BQ] & bishop_attacks) != 0:
                    continue

                rook_attacks: int = get_rook_moves_separate(target_square, occupancies_without_white_king)
                if (piece_array_local[BR] & rook_attacks) != 0:
                    continue

                if (piece_array_local[BQ] & rook_attacks) != 0:
                    continue

                move_list[move_count][MOVE_STARTING] = white_king_position
                move_list[move_count][MOVE_TARGET] = target_square
                move_list[move_count][MOVE_TAG] = TAG_NONE
                move_list[move_count][MOVE_PIECE] = WK
                move_count += 1

            # captures
            temp_captures = temp_attack & black_occupancies
            while temp_captures != 0:
                target_square = bitscan_forward(temp_captures)
                temp_captures &= temp_captures - 1

                if (piece_array_local[BP] & WHITE_PAWN_ATTACKS[target_square]) != 0:
                    continue

                if (piece_array_local[BN] & KNIGHT_ATTACKS[target_square]) != 0:
                    continue

                if (piece_array_local[BK] & KING_ATTACKS[target_square]) != 0:
                    continue

                bishop_attacks: int = get_bishop_moves_separate(target_square, occupancies_without_white_king)
                if (piece_array_local[BB] & bishop_attacks) != 0:
                    continue

                if (piece_array_local[BQ] & bishop_attacks) != 0:
                    continue

                rook_attacks: int = get_rook_moves_separate(target_square, occupancies_without_white_king)
                if (piece_array_local[BR] & rook_attacks) != 0:
                    continue

                if (piece_array_local[BQ] & rook_attacks) != 0:
                    continue

                move_list[move_count][MOVE_STARTING] = white_king_position
                move_list[move_count][MOVE_TARGET] = target_square
                move_list[move_count][MOVE_TAG] = TAG_CAPTURE
                move_list[move_count][MOVE_PIECE] = WK
                move_count += 1

            if white_king_check_count == 0:
                if (
                    (castle_rights[WKS_CASTLE_RIGHTS] and white_king_position == E1)  # king on e1
                    and ((WKS_EMPTY_BITBOARD & combined_occupancies) == 0)  # f1 and g1 empty
                    and ((piece_array_local[WR] & SQUARE_BBS[H1]) != 0)  #  rook on h1
                    and (not is_square_attacked_by_black(F1, combined_occupancies))
                    and (not is_square_attacked_by_black(G1, combined_occupancies))
                ):
                    move_list[move_count][MOVE_STARTING] = E1
                    move_list[move_count][MOVE_TARGET] = G1
                    move_list[move_count][MOVE_TAG] = TAG_WCASTLEKS
                    move_list[move_count][MOVE_PIECE] = WK
                    move_count += 1

                if (
                    (castle_rights[WQS_CASTLE_RIGHTS] and white_king_position == E1)  # king on e1
                    and ((WQS_EMPTY_BITBOARD & combined_occupancies) == 0)  # f1 and g1 empty
                    and ((piece_array_local[WR] & SQUARE_BBS[A1]) != 0)  # rook on A1
                    and (not is_square_attacked_by_black(C1, combined_occupancies))
                    and (not is_square_attacked_by_black(D1, combined_occupancies))
                ):
                    move_list[move_count][MOVE_STARTING] = E1
                    move_list[move_count][MOVE_TARGET] = C1
                    move_list[move_count][MOVE_TAG] = TAG_WCASTLEQS
                    move_list[move_count][MOVE_PIECE] = WK
                    move_count += 1

            temp_bitboard = piece_array_local[WN]

            while temp_bitboard != 0:
                starting_square = bitscan_forward(temp_bitboard)
                # removes the knight from that square to not infinitely loop
                temp_bitboard &= temp_bitboard - 1

                temp_pin_bitboard = MAX_ULONG
                if pin_number != 0:
                    for i in range(pin_number):
                        if pin_array[i][PINNED_SQUARE_INDEX] == starting_square:
                            temp_pin_bitboard = INBETWEEN_BITBOARDS[white_king_position][
                                pin_array[i][PINNING_PIECE_INDEX]
                            ]

                # gets knight captures
                temp_attack = (
                    (KNIGHT_ATTACKS[starting_square] & black_occupancies) & check_bitboard
                ) & temp_pin_bitboard
                while temp_attack != 0:
                    target_square = bitscan_forward(temp_attack)
                    temp_attack &= temp_attack - 1

                    move_list[move_count][MOVE_STARTING] = starting_square
                    move_list[move_count][MOVE_TARGET] = target_square
                    move_list[move_count][MOVE_TAG] = TAG_CAPTURE
                    move_list[move_count][MOVE_PIECE] = WN
                    move_count += 1

                temp_attack = (
                    (KNIGHT_ATTACKS[starting_square] & empty_occupancies) & check_bitboard
                ) & temp_pin_bitboard

                while temp_attack != 0:
                    target_square = bitscan_forward(temp_attack)
                    temp_attack &= temp_attack - 1

                    move_list[move_count][MOVE_STARTING] = starting_square
                    move_list[move_count][MOVE_TARGET] = target_square
                    move_list[move_count][MOVE_TAG] = TAG_NONE
                    move_list[move_count][MOVE_PIECE] = WN
                    move_count += 1

            temp_bitboard = piece_array_local[WP]

            while temp_bitboard != 0:
                starting_square = bitscan_forward(temp_bitboard)
                temp_bitboard &= temp_bitboard - 1

                temp_pin_bitboard = MAX_ULONG
                if pin_number != 0:
                    for i in range(pin_number):
                        if pin_array[i][PINNED_SQUARE_INDEX] == starting_square:
                            temp_pin_bitboard = INBETWEEN_BITBOARDS[white_king_position][
                                pin_array[i][PINNING_PIECE_INDEX]
                            ]

                # if up one square is empty
                if (SQUARE_BBS[starting_square - 8] & combined_occupancies) == 0:
                    if ((SQUARE_BBS[starting_square - 8] & check_bitboard) & temp_pin_bitboard) != 0:
                        # if promotion
                        if (SQUARE_BBS[starting_square] & RANK_7_BITBOARD) != 0:
                            move_list[move_count][MOVE_STARTING] = starting_square
                            move_list[move_count][MOVE_TARGET] = starting_square - 8
                            move_list[move_count][MOVE_TAG] = TAG_W_QUEEN_PROMOTION
                            move_list[move_count][MOVE_PIECE] = WP
                            move_count += 1

                            move_list[move_count][MOVE_STARTING] = starting_square
                            move_list[move_count][MOVE_TARGET] = starting_square - 8
                            move_list[move_count][MOVE_TAG] = TAG_W_ROOK_PROMOTION
                            move_list[move_count][MOVE_PIECE] = WP
                            move_count += 1

                            move_list[move_count][MOVE_STARTING] = starting_square
                            move_list[move_count][MOVE_TARGET] = starting_square - 8
                            move_list[move_count][MOVE_TAG] = TAG_W_BISHOP_PROMOTION
                            move_list[move_count][MOVE_PIECE] = WP
                            move_count += 1

                            move_list[move_count][MOVE_STARTING] = starting_square
                            move_list[move_count][MOVE_TARGET] = starting_square - 8
                            move_list[move_count][MOVE_TAG] = TAG_W_KNIGHT_PROMOTION
                            move_list[move_count][MOVE_PIECE] = WP
                            move_count += 1
                        else:
                            move_list[move_count][MOVE_STARTING] = starting_square
                            move_list[move_count][MOVE_TARGET] = starting_square - 8
                            move_list[move_count][MOVE_TAG] = TAG_NONE
                            move_list[move_count][MOVE_PIECE] = WP
                            move_count += 1
                    # if on rank 2
                    # fmt: off
                    if (
                        (SQUARE_BBS[starting_square] & RANK_2_BITBOARD) != 0
                        and ((SQUARE_BBS[starting_square - 16] & check_bitboard) & temp_pin_bitboard) != 0 # if not pinned or  # noqa: E501
                        and (((SQUARE_BBS[starting_square - 16]) & combined_occupancies) == 0) # if up two squares and one square are empty  # noqa: E501
                    ):
                        move_list[move_count][MOVE_STARTING] = starting_square
                        move_list[move_count][MOVE_TARGET] = starting_square - 16
                        move_list[move_count][MOVE_TAG] = TAG_DOUBLE_PAWN_WHITE
                        move_list[move_count][MOVE_PIECE] = WP
                        move_count += 1
                    # fmt: on

                # fmt: off
                # if black piece diagonal to pawn
                temp_attack = ((WHITE_PAWN_ATTACKS[starting_square] & black_occupancies) & check_bitboard) & temp_pin_bitboard # noqa: E501
                # fmt: on

                while temp_attack != 0:
                    target_square = bitscan_forward(temp_attack)
                    temp_attack &= temp_attack - 1

                    if (SQUARE_BBS[starting_square] & RANK_7_BITBOARD) != 0:  # if promotion
                        move_list[move_count][MOVE_STARTING] = starting_square
                        move_list[move_count][MOVE_TARGET] = target_square
                        move_list[move_count][MOVE_TAG] = TAG_W_CAPTURE_QUEEN_PROMOTION
                        move_list[move_count][MOVE_PIECE] = WP
                        move_count += 1

                        move_list[move_count][MOVE_STARTING] = starting_square
                        move_list[move_count][MOVE_TARGET] = target_square
                        move_list[move_count][MOVE_TAG] = TAG_W_CAPTURE_ROOK_PROMOTION
                        move_list[move_count][MOVE_PIECE] = WP
                        move_count += 1

                        move_list[move_count][MOVE_STARTING] = starting_square
                        move_list[move_count][MOVE_TARGET] = target_square
                        move_list[move_count][MOVE_TAG] = TAG_W_CAPTURE_BISHOP_PROMOTION
                        move_list[move_count][MOVE_PIECE] = WP
                        move_count += 1

                        move_list[move_count][MOVE_STARTING] = starting_square
                        move_list[move_count][MOVE_TARGET] = target_square
                        move_list[move_count][MOVE_TAG] = TAG_W_CAPTURE_KNIGHT_PROMOTION
                        move_list[move_count][MOVE_PIECE] = WP
                        move_count += 1
                    else:
                        move_list[move_count][MOVE_STARTING] = starting_square
                        move_list[move_count][MOVE_TARGET] = target_square
                        move_list[move_count][MOVE_TAG] = TAG_CAPTURE
                        move_list[move_count][MOVE_PIECE] = WP
                        move_count += 1
                # fmt: off
                if (((SQUARE_BBS[starting_square] & RANK_5_BITBOARD) != 0)  #check rank for ep
                    and (ep != NO_SQUARE)
                    and ((((WHITE_PAWN_ATTACKS[starting_square] & SQUARE_BBS[ep]) & check_bitboard) & temp_pin_bitboard) != 0)): # noqa: E501
                            # if no king on rank 5
                            if (piece_array_local[WK] & RANK_5_BITBOARD) == 0 or ((piece_array_local[BR] & RANK_5_BITBOARD) == 0 and (piece_array_local[BQ] & RANK_5_BITBOARD) == 0): # noqa: E501
                                move_list[move_count][MOVE_STARTING] = starting_square
                                move_list[move_count][MOVE_TARGET] = int(ep)
                                move_list[move_count][MOVE_TAG] = TAG_WHITEEP
                                move_list[move_count][MOVE_PIECE] = WP
                                move_count += 1
                            else:  #wk and br or bq on rank 5
                                occupancy_without_ep_pawns: int = combined_occupancies & ~SQUARE_BBS[starting_square]
                                occupancy_without_ep_pawns &= ~SQUARE_BBS[ep + 8]

                                rook_attacks_from_king: int = get_rook_moves_separate(white_king_position, occupancy_without_ep_pawns) # noqa: E501
                                # fmt: on

                                if (
                                    (rook_attacks_from_king & piece_array_local[BR]) == 0
                                    and (rook_attacks_from_king & piece_array_local[BQ]) == 0
                                    ):
                                    move_list[move_count][MOVE_STARTING] = starting_square
                                    move_list[move_count][MOVE_TARGET] = int(ep)
                                    move_list[move_count][MOVE_TAG] = TAG_WHITEEP
                                    move_list[move_count][MOVE_PIECE] = WP
                                    move_count += 1

            temp_bitboard = piece_array_local[WR]
            while temp_bitboard != 0:
                starting_square = bitscan_forward(temp_bitboard)
                temp_bitboard &= temp_bitboard - 1

                temp_pin_bitboard = MAX_ULONG
                if pin_number != 0:
                    for i in range(pin_number):
                        if pin_array[i][PINNED_SQUARE_INDEX] == starting_square:
                            temp_pin_bitboard = INBETWEEN_BITBOARDS[white_king_position][
                                pin_array[i][PINNING_PIECE_INDEX]
                            ]

                rook_attacks = get_rook_moves_separate(starting_square, combined_occupancies)
                temp_attack = ((rook_attacks & black_occupancies) & check_bitboard) & temp_pin_bitboard
                while temp_attack != 0:
                    target_square = bitscan_forward(temp_attack)
                    temp_attack &= temp_attack - 1

                    move_list[move_count][MOVE_STARTING] = starting_square
                    move_list[move_count][MOVE_TARGET] = target_square
                    move_list[move_count][MOVE_TAG] = TAG_CAPTURE
                    move_list[move_count][MOVE_PIECE] = WR
                    move_count += 1

                temp_attack = ((rook_attacks & empty_occupancies) & check_bitboard) & temp_pin_bitboard
                while temp_attack != 0:
                    target_square = bitscan_forward(temp_attack)
                    temp_attack &= temp_attack - 1

                    move_list[move_count][MOVE_STARTING] = starting_square
                    move_list[move_count][MOVE_TARGET] = target_square
                    move_list[move_count][MOVE_TAG] = TAG_NONE
                    move_list[move_count][MOVE_PIECE] = WR
                    move_count += 1

            temp_bitboard = piece_array_local[WB]
            while temp_bitboard != 0:
                starting_square = bitscan_forward(temp_bitboard)
                temp_bitboard &= temp_bitboard - 1

                temp_pin_bitboard = MAX_ULONG
                if pin_number != 0:
                    for i in range(pin_number):
                        if pin_array[i][PINNED_SQUARE_INDEX] == starting_square:
                            temp_pin_bitboard = INBETWEEN_BITBOARDS[white_king_position][
                                pin_array[i][PINNING_PIECE_INDEX]
                            ]

                bishop_attacks = get_bishop_moves_separate(starting_square, combined_occupancies)
                temp_attack = ((bishop_attacks & black_occupancies) & check_bitboard) & temp_pin_bitboard
                while temp_attack != 0:
                    target_square = bitscan_forward(temp_attack)
                    temp_attack &= temp_attack - 1

                    move_list[move_count][MOVE_STARTING] = starting_square
                    move_list[move_count][MOVE_TARGET] = target_square
                    move_list[move_count][MOVE_TAG] = TAG_CAPTURE
                    move_list[move_count][MOVE_PIECE] = WB
                    move_count += 1

                temp_attack = ((bishop_attacks & empty_occupancies) & check_bitboard) & temp_pin_bitboard
                while temp_attack != 0:
                    target_square = bitscan_forward(temp_attack)
                    temp_attack &= temp_attack - 1

                    move_list[move_count][MOVE_STARTING] = starting_square
                    move_list[move_count][MOVE_TARGET] = target_square
                    move_list[move_count][MOVE_TAG] = TAG_NONE
                    move_list[move_count][MOVE_PIECE] = WB
                    move_count += 1

            temp_bitboard = piece_array_local[WQ]
            while temp_bitboard != 0:
                starting_square = bitscan_forward(temp_bitboard)
                temp_bitboard &= temp_bitboard - 1

                temp_pin_bitboard = MAX_ULONG
                if pin_number != 0:
                    for i in range(pin_number):
                        if pin_array[i][PINNED_SQUARE_INDEX] == starting_square:
                            temp_pin_bitboard = INBETWEEN_BITBOARDS[white_king_position][
                                pin_array[i][PINNING_PIECE_INDEX]
                            ]

                queen_attacks = get_rook_moves_separate(starting_square, combined_occupancies)
                queen_attacks |= get_bishop_moves_separate(starting_square, combined_occupancies)

                temp_attack = ((queen_attacks & black_occupancies) & check_bitboard) & temp_pin_bitboard

                while temp_attack != 0:
                    target_square = bitscan_forward(temp_attack)
                    temp_attack &= temp_attack - 1

                    move_list[move_count][MOVE_STARTING] = starting_square
                    move_list[move_count][MOVE_TARGET] = target_square
                    move_list[move_count][MOVE_TAG] = TAG_CAPTURE
                    move_list[move_count][MOVE_PIECE] = WQ
                    move_count += 1

                temp_attack = ((queen_attacks & empty_occupancies) & check_bitboard) & temp_pin_bitboard
                while temp_attack != 0:
                    target_square = bitscan_forward(temp_attack)
                    temp_attack &= temp_attack - 1

                    move_list[move_count][MOVE_STARTING] = starting_square
                    move_list[move_count][MOVE_TARGET] = target_square
                    move_list[move_count][MOVE_TAG] = TAG_NONE
                    move_list[move_count][MOVE_PIECE] = WQ
                    move_count += 1

    else:  # black move
        black_king_check_count: int = 0
        black_king_position: int = bitscan_forward(piece_array_local[BK])

        # pawns
        temp_bitboard = piece_array_local[WP] & BLACK_PAWN_ATTACKS[black_king_position]
        if temp_bitboard != 0:
            pawn_square: int = bitscan_forward(temp_bitboard)
            check_bitboard = SQUARE_BBS[pawn_square]
            black_king_check_count += 1

        # knights
        temp_bitboard = piece_array_local[WN] & KNIGHT_ATTACKS[black_king_position]
        if temp_bitboard != 0:
            knight_square: int = bitscan_forward(temp_bitboard)
            check_bitboard = SQUARE_BBS[knight_square]
            black_king_check_count += 1

        # bishops
        bishop_attacks_checks: int = get_bishop_moves_separate(black_king_position, white_occupancies)
        temp_bitboard = piece_array_local[WB] & bishop_attacks_checks
        while temp_bitboard != 0:
            piece_square: int = bitscan_forward(temp_bitboard)
            temp_pin_bitboard = INBETWEEN_BITBOARDS[black_king_position][piece_square] & black_occupancies

            if temp_pin_bitboard == 0:
                check_bitboard = INBETWEEN_BITBOARDS[black_king_position][piece_square]
                black_king_check_count += 1
            else:
                pinned_square: int = bitscan_forward(temp_pin_bitboard)
                temp_pin_bitboard &= temp_pin_bitboard - 1

                if temp_pin_bitboard == 0:
                    pin_array[pin_number][PINNED_SQUARE_INDEX] = pinned_square
                    pin_array[pin_number][PINNING_PIECE_INDEX] = piece_square
                    pin_number += 1

            temp_bitboard &= temp_bitboard - 1

        # queen
        temp_bitboard = piece_array_local[WQ] & bishop_attacks_checks
        while temp_bitboard != 0:
            piece_square: int = bitscan_forward(temp_bitboard)
            temp_pin_bitboard = INBETWEEN_BITBOARDS[black_king_position][piece_square] & black_occupancies

            if temp_pin_bitboard == 0:
                check_bitboard = INBETWEEN_BITBOARDS[black_king_position][piece_square]
                black_king_check_count += 1
            else:
                pinned_square: int = bitscan_forward(temp_pin_bitboard)
                temp_pin_bitboard &= temp_pin_bitboard - 1

                if temp_pin_bitboard == 0:
                    pin_array[pin_number][PINNED_SQUARE_INDEX] = pinned_square
                    pin_array[pin_number][PINNING_PIECE_INDEX] = piece_square
                    pin_number += 1

            temp_bitboard &= temp_bitboard - 1

        # rook
        rook_attacks: int = get_rook_moves_separate(black_king_position, white_occupancies)
        temp_bitboard = piece_array_local[WR] & rook_attacks
        while temp_bitboard != 0:
            piece_square: int = bitscan_forward(temp_bitboard)
            temp_pin_bitboard = INBETWEEN_BITBOARDS[black_king_position][piece_square] & black_occupancies

            if temp_pin_bitboard == 0:
                check_bitboard = INBETWEEN_BITBOARDS[black_king_position][piece_square]
                black_king_check_count += 1
            else:
                pinned_square: int = bitscan_forward(temp_pin_bitboard)
                temp_pin_bitboard &= temp_pin_bitboard - 1

                if temp_pin_bitboard == 0:
                    pin_array[pin_number][PINNED_SQUARE_INDEX] = pinned_square
                    pin_array[pin_number][PINNING_PIECE_INDEX] = piece_square
                    pin_number += 1

            temp_bitboard &= temp_bitboard - 1

        # queen
        temp_bitboard = piece_array_local[WQ] & rook_attacks
        while temp_bitboard != 0:
            piece_square: int = bitscan_forward(temp_bitboard)
            temp_pin_bitboard = INBETWEEN_BITBOARDS[black_king_position][piece_square] & black_occupancies

            if temp_pin_bitboard == 0:
                check_bitboard = INBETWEEN_BITBOARDS[black_king_position][piece_square]
                black_king_check_count += 1
            else:
                pinned_square: int = bitscan_forward(temp_pin_bitboard)
                temp_pin_bitboard &= temp_pin_bitboard - 1

                if temp_pin_bitboard == 0:
                    pin_array[pin_number][PINNED_SQUARE_INDEX] = pinned_square
                    pin_array[pin_number][PINNING_PIECE_INDEX] = piece_square
                    pin_number += 1

            temp_bitboard &= temp_bitboard - 1

        if black_king_check_count > 1:
            occupancy_without_black_king: int = combined_occupancies & (~piece_array_local[BK])
            temp_attack = KING_ATTACKS[black_king_position] & white_occupancies

            while temp_attack != 0:
                target_square = bitscan_forward(temp_attack)
                temp_attack &= temp_attack - 1

                if (piece_array_local[WP] & BLACK_PAWN_ATTACKS[target_square]) != 0:
                    continue

                if (piece_array_local[WN] & KNIGHT_ATTACKS[target_square]) != 0:
                    continue

                if (piece_array_local[WK] & KING_ATTACKS[target_square]) != 0:
                    continue

                bishop_attacks: int = get_bishop_moves_separate(target_square, occupancy_without_black_king)
                if (piece_array_local[WB] & bishop_attacks) != 0:
                    continue

                if (piece_array_local[WQ] & bishop_attacks) != 0:
                    continue

                rook_attacks = get_rook_moves_separate(target_square, occupancy_without_black_king)
                if (piece_array_local[WR] & rook_attacks) != 0:
                    continue

                if (piece_array_local[WQ] & rook_attacks) != 0:
                    continue

                move_list[move_count][MOVE_STARTING] = starting_square
                move_list[move_count][MOVE_TARGET] = target_square
                move_list[move_count][MOVE_TAG] = TAG_CAPTURE
                move_list[move_count][MOVE_PIECE] = BK
                move_count += 1

            temp_attack = KING_ATTACKS[black_king_position] & ~combined_occupancies

            while temp_attack != 0:
                target_square = bitscan_forward(temp_attack)
                temp_attack &= temp_attack - 1

                if (piece_array_local[WP] & WHITE_PAWN_ATTACKS[target_square]) != 0:
                    continue

                if (piece_array_local[WN] & KNIGHT_ATTACKS[target_square]) != 0:
                    continue

                if (piece_array_local[WK] & KING_ATTACKS[target_square]) != 0:
                    continue

                bishop_attacks: int = get_bishop_moves_separate(target_square, occupancy_without_black_king)
                if (piece_array_local[WB] & bishop_attacks) != 0:
                    continue

                if (piece_array_local[WQ] & bishop_attacks) != 0:
                    continue

                rook_attacks: int = get_rook_moves_separate(target_square, occupancy_without_black_king)
                if (piece_array_local[WR] & rook_attacks) != 0:
                    continue

                if (piece_array_local[WQ] & rook_attacks) != 0:
                    continue

                move_list[move_count][MOVE_STARTING] = starting_square
                move_list[move_count][MOVE_TARGET] = target_square
                move_list[move_count][MOVE_TAG] = TAG_NONE
                move_list[move_count][MOVE_PIECE] = BK
                move_count += 1
        else:
            if black_king_check_count == 0:
                check_bitboard = MAX_ULONG

            temp_bitboard = piece_array_local[BP]

            while temp_bitboard != 0:
                starting_square = bitscan_forward(temp_bitboard)
                temp_bitboard &= temp_bitboard - 1

                temp_pin_bitboard = MAX_ULONG
                if pin_number != 0:
                    for i in range(pin_number):
                        if pin_array[i][PINNED_SQUARE_INDEX] == starting_square:
                            temp_pin_bitboard = INBETWEEN_BITBOARDS[black_king_position][
                                pin_array[i][PINNING_PIECE_INDEX]
                            ]

                # if up one square is empty
                if (SQUARE_BBS[starting_square + 8] & combined_occupancies) == 0:
                    if ((SQUARE_BBS[starting_square + 8] & check_bitboard) & temp_pin_bitboard) != 0:
                        # if promotion
                        if (SQUARE_BBS[starting_square] & RANK_2_BITBOARD) != 0:
                            move_list[move_count][MOVE_STARTING] = starting_square
                            move_list[move_count][MOVE_TARGET] = starting_square + 8
                            move_list[move_count][MOVE_TAG] = TAG_B_BISHOP_PROMOTION
                            move_list[move_count][MOVE_PIECE] = BP
                            move_count += 1

                            move_list[move_count][MOVE_STARTING] = starting_square
                            move_list[move_count][MOVE_TARGET] = starting_square + 8
                            move_list[move_count][MOVE_TAG] = TAG_B_KNIGHT_PROMOTION
                            move_list[move_count][MOVE_PIECE] = BP
                            move_count += 1

                            move_list[move_count][MOVE_STARTING] = starting_square
                            move_list[move_count][MOVE_TARGET] = starting_square + 8
                            move_list[move_count][MOVE_TAG] = TAG_B_ROOK_PROMOTION
                            move_list[move_count][MOVE_PIECE] = BP
                            move_count += 1

                            move_list[move_count][MOVE_STARTING] = starting_square
                            move_list[move_count][MOVE_TARGET] = starting_square + 8
                            move_list[move_count][MOVE_TAG] = TAG_B_QUEEN_PROMOTION
                            move_list[move_count][MOVE_PIECE] = BP
                            move_count += 1
                        else:
                            move_list[move_count][MOVE_STARTING] = starting_square
                            move_list[move_count][MOVE_TARGET] = starting_square + 8
                            move_list[move_count][MOVE_TAG] = TAG_NONE
                            move_list[move_count][MOVE_PIECE] = BP
                            move_count += 1
                    # fmt: off
                    # if on rank 2
                    if ((SQUARE_BBS[starting_square] & RANK_7_BITBOARD) != 0
                        and ((SQUARE_BBS[starting_square+16] & check_bitboard) & temp_pin_bitboard) != 0
                        and ((SQUARE_BBS[starting_square+16]) & combined_occupancies) == 0
                    ): # if up two squares and one square are empty
                                move_list[move_count][MOVE_STARTING] = starting_square
                                move_list[move_count][MOVE_TARGET] = starting_square + 16
                                move_list[move_count][MOVE_TAG] = TAG_DOUBLE_PAWN_BLACK
                                move_list[move_count][MOVE_PIECE] = BP
                                move_count += 1
                    # fmt: on

                # fmt: off
                # if black piece diagonal to pawn
                temp_attack = ((BLACK_PAWN_ATTACKS[starting_square] & white_occupancies) & check_bitboard) & temp_pin_bitboard # noqa: E501
                # fmt: on

                while temp_attack != 0:
                    target_square = bitscan_forward(temp_attack)  # find the bit
                    temp_attack &= temp_attack - 1

                    # if promotion
                    if (SQUARE_BBS[starting_square] & RANK_2_BITBOARD) != 0:
                        move_list[move_count][MOVE_STARTING] = starting_square
                        move_list[move_count][MOVE_TARGET] = target_square
                        move_list[move_count][MOVE_TAG] = TAG_B_CAPTURE_QUEEN_PROMOTION
                        move_list[move_count][MOVE_PIECE] = BP
                        move_count += 1

                        move_list[move_count][MOVE_STARTING] = starting_square
                        move_list[move_count][MOVE_TARGET] = target_square
                        move_list[move_count][MOVE_TAG] = TAG_B_CAPTURE_ROOK_PROMOTION
                        move_list[move_count][MOVE_PIECE] = BP
                        move_count += 1

                        move_list[move_count][MOVE_STARTING] = starting_square
                        move_list[move_count][MOVE_TARGET] = target_square
                        move_list[move_count][MOVE_TAG] = TAG_B_CAPTURE_KNIGHT_PROMOTION
                        move_list[move_count][MOVE_PIECE] = BP
                        move_count += 1

                        move_list[move_count][MOVE_STARTING] = starting_square
                        move_list[move_count][MOVE_TARGET] = target_square
                        move_list[move_count][MOVE_TAG] = TAG_B_CAPTURE_BISHOP_PROMOTION
                        move_list[move_count][MOVE_PIECE] = BP
                        move_count += 1
                    else:
                        move_list[move_count][MOVE_STARTING] = starting_square
                        move_list[move_count][MOVE_TARGET] = target_square
                        move_list[move_count][MOVE_TAG] = TAG_CAPTURE
                        move_list[move_count][MOVE_PIECE] = BP
                        move_count += 1

                # fmt: off
                if (((SQUARE_BBS[starting_square] & RANK_4_BITBOARD) != 0)  #check rank for ep
                    and (ep != NO_SQUARE)
                    and ((((BLACK_PAWN_ATTACKS[starting_square] & SQUARE_BBS[ep]) & check_bitboard) & temp_pin_bitboard) != 0) # noqa: E501
                ):
                    # if no king on rank 5
                    if (piece_array_local[BK] & RANK_4_BITBOARD) == 0 or ((piece_array_local[WR]&RANK_4_BITBOARD) == 0 and (piece_array_local[WQ]&RANK_4_BITBOARD) == 0): # noqa: E501

                        move_list[move_count][MOVE_STARTING] = starting_square
                        move_list[move_count][MOVE_TARGET] = int(ep)
                        move_list[move_count][MOVE_TAG] = TAG_BLACKEP
                        move_list[move_count][MOVE_PIECE] = BP
                        move_count += 1
                    else:  #wk and br or bq on rank 5
                        occupancy_without_ep_pawns = combined_occupancies & ~SQUARE_BBS[starting_square]
                        occupancy_without_ep_pawns &= ~SQUARE_BBS[ep-8]

                        rook_attacks_from_king = get_rook_moves_separate(black_king_position, occupancy_without_ep_pawns) # noqa: E501

                        if ((rook_attacks_from_king & piece_array_local[WR]) == 0
                            and (rook_attacks_from_king & piece_array_local[WQ]) == 0):
                            move_list[move_count][MOVE_STARTING] = starting_square
                            move_list[move_count][MOVE_TARGET] = int(ep)
                            move_list[move_count][MOVE_TAG] = TAG_BLACKEP
                            move_list[move_count][MOVE_PIECE] = BP
                            move_count += 1
                # fmt: on

            temp_bitboard = piece_array_local[BN]

            while temp_bitboard != 0:
                # looks for the starting_square
                starting_square = bitscan_forward(temp_bitboard)
                # removes the knight from that square to not infinitely loop
                temp_bitboard &= temp_bitboard - 1

                temp_pin_bitboard = MAX_ULONG
                if pin_number != 0:
                    for i in range(pin_number):
                        if pin_array[i][PINNED_SQUARE_INDEX] == starting_square:
                            temp_pin_bitboard = INBETWEEN_BITBOARDS[black_king_position][
                                pin_array[i][PINNING_PIECE_INDEX]
                            ]

                # gets knight captures
                temp_attack = (
                    (KNIGHT_ATTACKS[starting_square] & white_occupancies) & check_bitboard
                ) & temp_pin_bitboard
                while temp_attack != 0:
                    target_square = bitscan_forward(temp_attack)
                    temp_attack &= temp_attack - 1

                    move_list[move_count][MOVE_STARTING] = starting_square
                    move_list[move_count][MOVE_TARGET] = target_square
                    move_list[move_count][MOVE_TAG] = TAG_CAPTURE
                    move_list[move_count][MOVE_PIECE] = BN
                    move_count += 1

                # fmt: off
                temp_attack = ((KNIGHT_ATTACKS[starting_square] & (~combined_occupancies)) & check_bitboard) & temp_pin_bitboard  # noqa: E501
                while temp_attack != 0:
                    target_square = bitscan_forward(temp_attack)
                    temp_attack &= temp_attack - 1
                    move_list[move_count][MOVE_STARTING] = starting_square
                    move_list[move_count][MOVE_TARGET] = target_square
                    move_list[move_count][MOVE_TAG] = TAG_NONE
                    move_list[move_count][MOVE_PIECE] = BN
                    move_count += 1
                # fmt: on

            temp_bitboard = piece_array_local[BB]
            while temp_bitboard != 0:
                starting_square = bitscan_forward(temp_bitboard)
                temp_bitboard &= temp_bitboard - 1

                temp_pin_bitboard = MAX_ULONG
                if pin_number != 0:
                    for i in range(pin_number):
                        if pin_array[i][PINNED_SQUARE_INDEX] == starting_square:
                            temp_pin_bitboard = INBETWEEN_BITBOARDS[black_king_position][
                                pin_array[i][PINNING_PIECE_INDEX]
                            ]

                bishop_attacks = get_bishop_moves_separate(starting_square, combined_occupancies)

                temp_attack = ((bishop_attacks & white_occupancies) & check_bitboard) & temp_pin_bitboard
                while temp_attack != 0:
                    target_square = bitscan_forward(temp_attack)
                    temp_attack &= temp_attack - 1

                    move_list[move_count][MOVE_STARTING] = starting_square
                    move_list[move_count][MOVE_TARGET] = target_square
                    move_list[move_count][MOVE_TAG] = TAG_CAPTURE
                    move_list[move_count][MOVE_PIECE] = BB
                    move_count += 1

                temp_attack = ((bishop_attacks & (~combined_occupancies)) & check_bitboard) & temp_pin_bitboard
                while temp_attack != 0:
                    target_square = bitscan_forward(temp_attack)
                    temp_attack &= temp_attack - 1

                    move_list[move_count][MOVE_STARTING] = starting_square
                    move_list[move_count][MOVE_TARGET] = target_square
                    move_list[move_count][MOVE_TAG] = TAG_NONE
                    move_list[move_count][MOVE_PIECE] = BB
                    move_count += 1

            temp_bitboard = piece_array_local[BR]
            while temp_bitboard != 0:
                starting_square = bitscan_forward(temp_bitboard)
                temp_bitboard &= temp_bitboard - 1

                temp_pin_bitboard = MAX_ULONG
                if pin_number != 0:
                    for i in range(pin_number):
                        if pin_array[i][PINNED_SQUARE_INDEX] == starting_square:
                            temp_pin_bitboard = INBETWEEN_BITBOARDS[black_king_position][
                                pin_array[i][PINNING_PIECE_INDEX]
                            ]

                rook_attacks = get_rook_moves_separate(starting_square, combined_occupancies)

                temp_attack = ((rook_attacks & white_occupancies) & check_bitboard) & temp_pin_bitboard
                while temp_attack != 0:
                    target_square = bitscan_forward(temp_attack)
                    temp_attack &= temp_attack - 1

                    move_list[move_count][MOVE_STARTING] = starting_square
                    move_list[move_count][MOVE_TARGET] = target_square
                    move_list[move_count][MOVE_TAG] = TAG_CAPTURE
                    move_list[move_count][MOVE_PIECE] = BR
                    move_count += 1

                temp_attack = ((rook_attacks & (~combined_occupancies)) & check_bitboard) & temp_pin_bitboard
                while temp_attack != 0:
                    target_square = bitscan_forward(temp_attack)
                    temp_attack &= temp_attack - 1

                    move_list[move_count][MOVE_STARTING] = starting_square
                    move_list[move_count][MOVE_TARGET] = target_square
                    move_list[move_count][MOVE_TAG] = TAG_NONE
                    move_list[move_count][MOVE_PIECE] = BR
                    move_count += 1

            temp_bitboard = piece_array_local[BQ]
            while temp_bitboard != 0:
                starting_square = bitscan_forward(temp_bitboard)
                temp_bitboard &= temp_bitboard - 1

                temp_pin_bitboard = MAX_ULONG
                if pin_number != 0:
                    for i in range(pin_number):
                        if pin_array[i][PINNED_SQUARE_INDEX] == starting_square:
                            temp_pin_bitboard = INBETWEEN_BITBOARDS[black_king_position][
                                pin_array[i][PINNING_PIECE_INDEX]
                            ]

                queen_attacks = get_rook_moves_separate(starting_square, combined_occupancies)
                queen_attacks |= get_bishop_moves_separate(starting_square, combined_occupancies)
                temp_attack = ((queen_attacks & white_occupancies) & check_bitboard) & temp_pin_bitboard

                while temp_attack != 0:
                    target_square = bitscan_forward(temp_attack)
                    temp_attack &= temp_attack - 1

                    move_list[move_count][MOVE_STARTING] = starting_square
                    move_list[move_count][MOVE_TARGET] = target_square
                    move_list[move_count][MOVE_TAG] = TAG_CAPTURE
                    move_list[move_count][MOVE_PIECE] = BQ
                    move_count += 1

                temp_attack = ((queen_attacks & (~combined_occupancies)) & check_bitboard) & temp_pin_bitboard

                while temp_attack != 0:
                    target_square = bitscan_forward(temp_attack)
                    temp_attack &= temp_attack - 1

                    move_list[move_count][MOVE_STARTING] = starting_square
                    move_list[move_count][MOVE_TARGET] = target_square
                    move_list[move_count][MOVE_TAG] = TAG_NONE
                    move_list[move_count][MOVE_PIECE] = BQ
                    move_count += 1

            # gets knight captures
            temp_attack = KING_ATTACKS[black_king_position] & white_occupancies
            while temp_attack != 0:
                target_square = bitscan_forward(temp_attack)
                temp_attack &= temp_attack - 1

                if (piece_array_local[WP] & BLACK_PAWN_ATTACKS[target_square]) != 0:
                    continue

                if (piece_array_local[WN] & KNIGHT_ATTACKS[target_square]) != 0:
                    continue

                if (piece_array_local[WK] & KING_ATTACKS[target_square]) != 0:
                    continue

                occupancy_without_black_king = combined_occupancies & (~piece_array_local[BK])
                bishop_attacks = get_bishop_moves_separate(target_square, occupancy_without_black_king)
                if (piece_array_local[WB] & bishop_attacks) != 0:
                    continue

                if (piece_array_local[WQ] & bishop_attacks) != 0:
                    continue

                rook_attacks = get_rook_moves_separate(target_square, occupancy_without_black_king)
                if (piece_array_local[WR] & rook_attacks) != 0:
                    continue

                if (piece_array_local[WQ] & rook_attacks) != 0:
                    continue

                move_list[move_count][MOVE_STARTING] = black_king_position
                move_list[move_count][MOVE_TARGET] = target_square
                move_list[move_count][MOVE_TAG] = TAG_CAPTURE
                move_list[move_count][MOVE_PIECE] = BK
                move_count += 1

            # get knight moves to empty squares
            temp_attack = KING_ATTACKS[black_king_position] & (~combined_occupancies)

            while temp_attack != 0:
                target_square = bitscan_forward(temp_attack)
                temp_attack &= temp_attack - 1

                if (piece_array_local[WP] & BLACK_PAWN_ATTACKS[target_square]) != 0:
                    continue

                if (piece_array_local[WN] & KNIGHT_ATTACKS[target_square]) != 0:
                    continue

                if (piece_array_local[WK] & KING_ATTACKS[target_square]) != 0:
                    continue

                occupancy_without_black_king: int = combined_occupancies & (~piece_array_local[BK])
                bishop_attacks = get_bishop_moves_separate(target_square, occupancy_without_black_king)
                if (piece_array_local[WB] & bishop_attacks) != 0:
                    continue

                if (piece_array_local[WQ] & bishop_attacks) != 0:
                    continue

                rook_attacks = get_rook_moves_separate(target_square, occupancy_without_black_king)
                if (piece_array_local[WR] & rook_attacks) != 0:
                    continue

                if (piece_array_local[WQ] & rook_attacks) != 0:
                    continue

                move_list[move_count][MOVE_STARTING] = black_king_position
                move_list[move_count][MOVE_TARGET] = target_square
                move_list[move_count][MOVE_TAG] = TAG_NONE
                move_list[move_count][MOVE_PIECE] = BK
                move_count += 1

        # fmt: off
        if black_king_check_count == 0:
            if (castle_rights[BKS_CASTLE_RIGHTS] and black_king_position == E8 # king on e1
                and (BKS_EMPTY_BITBOARD & combined_occupancies) == 0 # f1 and g1 empty
                and (piece_array_local[BR] & SQUARE_BBS[H8]) != 0 # rook on h8
                and not is_square_attacked_by_white(F8, combined_occupancies)
                and not is_square_attacked_by_white(G8, combined_occupancies)
            ):
                move_list[move_count][MOVE_STARTING] = E8
                move_list[move_count][MOVE_TARGET] = G8
                move_list[move_count][MOVE_TAG] = TAG_BCASTLEKS
                move_list[move_count][MOVE_PIECE] = BK
                move_count += 1


            if (castle_rights[BQS_CASTLE_RIGHTS] and black_king_position == E8 # king on e1
                and (BQS_EMPTY_BITBOARD & combined_occupancies) == 0  # f1 and g1 empty
                and (piece_array_local[BR] & SQUARE_BBS[A8]) != 0  # rook on a8
                and not is_square_attacked_by_white(C8, combined_occupancies)
                and not is_square_attacked_by_white(D8, combined_occupancies)
            ):
                move_list[move_count][MOVE_STARTING] = E8
                move_list[move_count][MOVE_TARGET] = C8
                move_list[move_count][MOVE_TAG] = TAG_BCASTLEQS
                move_list[move_count][MOVE_PIECE] = BK
                move_count += 1

    if depth == 1:
        return move_count

    nodes: int = 0
    prior_nodes: int
    copy_ep: int = ep
    copy_castle: list[bool] = [castle_rights[0], castle_rights[1], castle_rights[2], castle_rights[3]]

    for move_index in range(move_count):
        starting_square: int = move_list[move_index][MOVE_STARTING]
        target_square: int = move_list[move_index][MOVE_TARGET]
        piece: int = move_list[move_index][MOVE_PIECE]
        tag: int = move_list[move_index][MOVE_TAG]

        capture_index: int = -1

        white_to_play = not white_to_play

        match tag:
            case 0:  # none
                piece_array[piece] |= SQUARE_BBS[target_square]
                piece_array[piece] &= ~SQUARE_BBS[starting_square]
                ep = NO_SQUARE
            case 26:  # check
                piece_array[piece] |= SQUARE_BBS[target_square]
                piece_array[piece] &= ~SQUARE_BBS[starting_square]
                ep = NO_SQUARE
            case 1:  # capture
                piece_array[piece] |= SQUARE_BBS[target_square]
                piece_array[piece] &= ~SQUARE_BBS[starting_square]
                if piece >= WP and piece <= WK:
                    for i in range(BP, BK + 1):
                        if (piece_array[i] & SQUARE_BBS[target_square]) != 0:
                            capture_index = i
                            break
                    piece_array[capture_index] &= ~SQUARE_BBS[target_square]
                else:  # is black
                    for i in range(WP, BP):
                        if (piece_array[i] & SQUARE_BBS[target_square]) != 0:
                            capture_index = i
                            break
                    piece_array[capture_index] &= ~SQUARE_BBS[target_square]
                ep = NO_SQUARE
            case 27:  # check cap
                piece_array[piece] |= SQUARE_BBS[target_square]
                piece_array[piece] &= ~SQUARE_BBS[starting_square]
                if piece >= 0 and piece <= WK:
                    for i in range(BP, BK + 1):
                        if (piece_array[i] & SQUARE_BBS[target_square]) != 0:
                            capture_index = i
                            break
                    piece_array[capture_index] &= ~SQUARE_BBS[target_square]
                else:  # is black
                    for i in range(WP, BP):
                        if (piece_array[i] & SQUARE_BBS[target_square]) != 0:
                            capture_index = i
                            break
                    piece_array[capture_index] &= ~SQUARE_BBS[target_square]
                ep = NO_SQUARE
            case 2:  # white ep
                # move piece
                piece_array[WP] |= SQUARE_BBS[target_square]
                piece_array[WP] &= ~SQUARE_BBS[starting_square]
                # remove
                piece_array[BP] &= ~SQUARE_BBS[target_square + 8]
                ep = NO_SQUARE
            case 3:  # black ep
                # move piece
                piece_array[BP] |= SQUARE_BBS[target_square]
                piece_array[BP] &= ~SQUARE_BBS[starting_square]
                # remove white pawn square up
                piece_array[WP] &= ~SQUARE_BBS[target_square - 8]
                ep = NO_SQUARE
            case 4:  # WKS
                # white king
                piece_array[WK] |= SQUARE_BBS[G1]
                piece_array[WK] &= ~SQUARE_BBS[E1]
                # white rook
                piece_array[WR] |= SQUARE_BBS[F1]
                piece_array[WR] &= ~SQUARE_BBS[H1]
                # occupancies
                castle_rights[WKS_CASTLE_RIGHTS] = False
                castle_rights[WQS_CASTLE_RIGHTS] = False
                ep = NO_SQUARE
            case 5:  # WQS
                # white king
                piece_array[WK] |= SQUARE_BBS[C1]
                piece_array[WK] &= ~SQUARE_BBS[E1]
                # white rook
                piece_array[WR] |= SQUARE_BBS[D1]
                piece_array[WR] &= ~SQUARE_BBS[A1]

                castle_rights[WKS_CASTLE_RIGHTS] = False
                castle_rights[WQS_CASTLE_RIGHTS] = False
                ep = NO_SQUARE
            case 6:  # BKS
                # white king
                piece_array[BK] |= SQUARE_BBS[G8]
                piece_array[BK] &= ~SQUARE_BBS[E8]
                # white rook
                piece_array[BR] |= SQUARE_BBS[F8]
                piece_array[BR] &= ~SQUARE_BBS[H8]
                castle_rights[BKS_CASTLE_RIGHTS] = False
                castle_rights[BQS_CASTLE_RIGHTS] = False
                ep = NO_SQUARE
            case 7:  # BQS
                # white king
                piece_array[BK] |= SQUARE_BBS[C8]
                piece_array[BK] &= ~SQUARE_BBS[E8]
                # white rook
                piece_array[BR] |= SQUARE_BBS[D8]
                piece_array[BR] &= ~SQUARE_BBS[A8]
                castle_rights[BKS_CASTLE_RIGHTS] = False
                castle_rights[BQS_CASTLE_RIGHTS] = False
                ep = NO_SQUARE
            case 8:  # BNPr
                piece_array[BN] |= SQUARE_BBS[target_square]
                piece_array[piece] &= ~SQUARE_BBS[starting_square]
                ep = NO_SQUARE
            case 9:  # BBPr
                piece_array[BB] |= SQUARE_BBS[target_square]
                piece_array[piece] &= ~SQUARE_BBS[starting_square]
                ep = NO_SQUARE
            case 10:  # BQPr
                piece_array[BQ] |= SQUARE_BBS[target_square]
                piece_array[piece] &= ~SQUARE_BBS[starting_square]
                ep = NO_SQUARE
            case 11:  # BRPr
                piece_array[BR] |= SQUARE_BBS[target_square]
                piece_array[piece] &= ~SQUARE_BBS[starting_square]
                ep = NO_SQUARE
            case 12:  # WNPr
                piece_array[WN] |= SQUARE_BBS[target_square]
                piece_array[piece] &= ~SQUARE_BBS[starting_square]
                ep = NO_SQUARE
            case 13:  # WBPr
                piece_array[WB] |= SQUARE_BBS[target_square]
                piece_array[piece] &= ~SQUARE_BBS[starting_square]
                ep = NO_SQUARE
            case 14:  # WQPr
                piece_array[WQ] |= SQUARE_BBS[target_square]
                piece_array[piece] &= ~SQUARE_BBS[starting_square]
                ep = NO_SQUARE
            case 15:  # WRPr
                piece_array[WR] |= SQUARE_BBS[target_square]
                piece_array[piece] &= ~SQUARE_BBS[starting_square]
                ep = NO_SQUARE
            case 16:  # BNPrCAP
                piece_array[BN] |= SQUARE_BBS[target_square]
                piece_array[piece] &= ~SQUARE_BBS[starting_square]
                ep = NO_SQUARE
                for i in range(WP, BP):
                    if (piece_array[i] & SQUARE_BBS[target_square]) != 0:
                        capture_index = i
                        break

                piece_array[capture_index] &= ~SQUARE_BBS[target_square]
            case 17:  # BBPrCAP
                piece_array[BB] |= SQUARE_BBS[target_square]
                piece_array[piece] &= ~SQUARE_BBS[starting_square]
                ep = NO_SQUARE
                for i in range(WP, BP):
                    if (piece_array[i] & SQUARE_BBS[target_square]) != 0:
                        capture_index = i
                        break
                piece_array[capture_index] &= ~SQUARE_BBS[target_square]
            case 18:  # BQPrCAP
                piece_array[BQ] |= SQUARE_BBS[target_square]
                piece_array[piece] &= ~SQUARE_BBS[starting_square]
                ep = NO_SQUARE
                for i in range(WP, BP):
                    if (piece_array[i] & SQUARE_BBS[target_square]) != 0:
                        capture_index = i
                        break
                piece_array[capture_index] &= ~SQUARE_BBS[target_square]
            case 19:  # BRPrCAP
                piece_array[BR] |= SQUARE_BBS[target_square]
                piece_array[piece] &= ~SQUARE_BBS[starting_square]
                ep = NO_SQUARE
                for i in range(WP, BP):
                    if (piece_array[i] & SQUARE_BBS[target_square]) != 0:
                        capture_index = i
                        break
                piece_array[capture_index] &= ~SQUARE_BBS[target_square]
            case 20:  # WNPrCAP
                piece_array[WN] |= SQUARE_BBS[target_square]
                piece_array[piece] &= ~SQUARE_BBS[starting_square]
                ep = NO_SQUARE
                for i in range(BP, BK + 1):
                    if (piece_array[i] & SQUARE_BBS[target_square]) != 0:
                        capture_index = i
                        break
                piece_array[capture_index] &= ~SQUARE_BBS[target_square]
            case 21:  # WBPrCAP
                piece_array[WB] |= SQUARE_BBS[target_square]
                piece_array[piece] &= ~SQUARE_BBS[starting_square]
                ep = NO_SQUARE
                for i in range(BP, BK + 1):
                    if (piece_array[i] & SQUARE_BBS[target_square]) != 0:
                        capture_index = i
                        break
                piece_array[capture_index] &= ~SQUARE_BBS[target_square]
            case 22:  # WQPrCAP
                piece_array[WQ] |= SQUARE_BBS[target_square]
                piece_array[piece] &= ~SQUARE_BBS[starting_square]
                ep = NO_SQUARE
                for i in range(BP, BK + 1):
                    if (piece_array[i] & SQUARE_BBS[target_square]) != 0:
                        capture_index = i
                        break
                piece_array[capture_index] &= ~SQUARE_BBS[target_square]
            case 23:  # WRPrCAP
                piece_array[WR] |= SQUARE_BBS[target_square]
                piece_array[piece] &= ~SQUARE_BBS[starting_square]
                ep = NO_SQUARE
                for i in range(BP, BK + 1):
                    if (piece_array[i] & SQUARE_BBS[target_square]) != 0:
                        capture_index = i
                        break
                piece_array[capture_index] &= ~SQUARE_BBS[target_square]
            case 24:  # WDouble
                piece_array[WP] |= SQUARE_BBS[target_square]
                piece_array[WP] &= ~SQUARE_BBS[starting_square]
                ep = target_square + 8
            case 25:  # BDouble
                piece_array[BP] |= SQUARE_BBS[target_square]
                piece_array[BP] &= ~SQUARE_BBS[starting_square]
                ep = target_square - 8

        if piece == WK:
            castle_rights[WKS_CASTLE_RIGHTS] = False
            castle_rights[WQS_CASTLE_RIGHTS] = False
        elif piece == BK:
            castle_rights[BKS_CASTLE_RIGHTS] = False
            castle_rights[BQS_CASTLE_RIGHTS] = False
        elif piece == WR:
            if castle_rights[WKS_CASTLE_RIGHTS] and (piece_array[WR] & SQUARE_BBS[H1]) == 0:
                castle_rights[WKS_CASTLE_RIGHTS] = False
            if castle_rights[WQS_CASTLE_RIGHTS] and (piece_array[WR] & SQUARE_BBS[A1]) == 0:
                castle_rights[WQS_CASTLE_RIGHTS] = False
        elif piece == BR:
            if castle_rights[BKS_CASTLE_RIGHTS] and (piece_array[BR] & SQUARE_BBS[H8]) == 0:
                castle_rights[BKS_CASTLE_RIGHTS] = False
            if castle_rights[BQS_CASTLE_RIGHTS] and (piece_array[BR] & SQUARE_BBS[A8]) == 0:
                castle_rights[BQS_CASTLE_RIGHTS] = False

        prior_nodes = nodes
        nodes += perft_inline(depth - 1, ply + 1)

        white_to_play = not white_to_play
        match tag:
            case 0:  # none
                piece_array[piece] |= SQUARE_BBS[starting_square]
                piece_array[piece] &= ~SQUARE_BBS[target_square]
            case 26:  # check
                piece_array[piece] |= SQUARE_BBS[starting_square]
                piece_array[piece] &= ~SQUARE_BBS[target_square]
            case 1:  # capture
                piece_array[piece] |= SQUARE_BBS[starting_square]
                piece_array[piece] &= ~SQUARE_BBS[target_square]
                if piece >= WP and piece < BP:
                    piece_array[capture_index] |= SQUARE_BBS[target_square]
                else:  # is black
                    piece_array[capture_index] |= SQUARE_BBS[target_square]
            case 27:  # check cap
                piece_array[piece] |= SQUARE_BBS[starting_square]
                piece_array[piece] &= ~SQUARE_BBS[target_square]
                if piece >= WP and piece < BP:
                    piece_array[capture_index] |= SQUARE_BBS[target_square]
                else:  # is black
                    piece_array[capture_index] |= SQUARE_BBS[target_square]
            case 2:  # white ep
                piece_array[WP] |= SQUARE_BBS[starting_square]
                piece_array[WP] &= ~SQUARE_BBS[target_square]
                piece_array[BP] |= SQUARE_BBS[target_square + 8]
            case 3:  # black ep
                piece_array[BP] |= SQUARE_BBS[starting_square]
                piece_array[BP] &= ~SQUARE_BBS[target_square]
                piece_array[WP] |= SQUARE_BBS[target_square - 8]
            case 4:  # WKS
                # white king
                piece_array[WK] |= SQUARE_BBS[E1]
                piece_array[WK] &= ~SQUARE_BBS[G1]
                # white rook
                piece_array[WR] |= SQUARE_BBS[H1]
                piece_array[WR] &= ~SQUARE_BBS[F1]
            case 5:  # WQS
                # white king
                piece_array[WK] |= SQUARE_BBS[E1]
                piece_array[WK] &= ~SQUARE_BBS[C1]
                # white rook
                piece_array[WR] |= SQUARE_BBS[A1]
                piece_array[WR] &= ~SQUARE_BBS[D1]
            case 6:  # BKS
                # white king
                piece_array[BK] |= SQUARE_BBS[E8]
                piece_array[BK] &= ~SQUARE_BBS[G8]
                # white rook
                piece_array[BR] |= SQUARE_BBS[H8]
                piece_array[BR] &= ~SQUARE_BBS[F8]
            case 7:  # BQS
                # white king
                piece_array[BK] |= SQUARE_BBS[E8]
                piece_array[BK] &= ~SQUARE_BBS[C8]
                # white rook
                piece_array[BR] |= SQUARE_BBS[A8]
                piece_array[BR] &= ~SQUARE_BBS[D8]
            case 8:  # BNPr
                piece_array[BP] |= SQUARE_BBS[starting_square]
                piece_array[BN] &= ~SQUARE_BBS[target_square]
            case 9:  # BBPr
                piece_array[BP] |= SQUARE_BBS[starting_square]
                piece_array[BB] &= ~SQUARE_BBS[target_square]
            case 10:  # BQPr
                piece_array[BP] |= SQUARE_BBS[starting_square]
                piece_array[BQ] &= ~SQUARE_BBS[target_square]
            case 11:  # BRPr
                piece_array[BP] |= SQUARE_BBS[starting_square]
                piece_array[BR] &= ~SQUARE_BBS[target_square]
            case 12:  # WNPr
                piece_array[WP] |= SQUARE_BBS[starting_square]
                piece_array[WN] &= ~SQUARE_BBS[target_square]
            case 13:  # WBPr
                piece_array[WP] |= SQUARE_BBS[starting_square]
                piece_array[WB] &= ~SQUARE_BBS[target_square]
            case 14:  # WQPr
                piece_array[WP] |= SQUARE_BBS[starting_square]
                piece_array[WQ] &= ~SQUARE_BBS[target_square]
            case 15:  # WRPr
                piece_array[WP] |= SQUARE_BBS[starting_square]
                piece_array[WR] &= ~SQUARE_BBS[target_square]
            case 16:  # BNPrCAP
                piece_array[BP] |= SQUARE_BBS[starting_square]
                piece_array[BN] &= ~SQUARE_BBS[target_square]
                piece_array[capture_index] |= SQUARE_BBS[target_square]
            case 17:  # BBPrCAP
                piece_array[BP] |= SQUARE_BBS[starting_square]
                piece_array[BB] &= ~SQUARE_BBS[target_square]
                piece_array[capture_index] |= SQUARE_BBS[target_square]
            case 18:  # BQPrCAP
                piece_array[BP] |= SQUARE_BBS[starting_square]
                piece_array[BQ] &= ~SQUARE_BBS[target_square]
                piece_array[capture_index] |= SQUARE_BBS[target_square]
            case 19:  # BRPrCAP
                piece_array[BP] |= SQUARE_BBS[starting_square]
                piece_array[BR] &= ~SQUARE_BBS[target_square]
                piece_array[capture_index] |= SQUARE_BBS[target_square]
            case 20:  # WNPrCAP
                piece_array[WP] |= SQUARE_BBS[starting_square]
                piece_array[WN] &= ~SQUARE_BBS[target_square]
                piece_array[capture_index] |= SQUARE_BBS[target_square]
            case 21:  # WBPrCAP
                piece_array[WP] |= SQUARE_BBS[starting_square]
                piece_array[WB] &= ~SQUARE_BBS[target_square]
                piece_array[capture_index] |= SQUARE_BBS[target_square]
            case 22:  # WQPrCAP
                piece_array[WP] |= SQUARE_BBS[starting_square]
                piece_array[WQ] &= ~SQUARE_BBS[target_square]
                piece_array[capture_index] |= SQUARE_BBS[target_square]
            case 23:  # WRPrCAP
                piece_array[WP] |= SQUARE_BBS[starting_square]
                piece_array[WR] &= ~SQUARE_BBS[target_square]
                piece_array[capture_index] |= SQUARE_BBS[target_square]
            case 24:  # WDouble
                piece_array[WP] |= SQUARE_BBS[starting_square]
                piece_array[WP] &= ~SQUARE_BBS[target_square]
            case 25:  # BDouble
                piece_array[BP] |= SQUARE_BBS[starting_square]
                piece_array[BP] &= ~SQUARE_BBS[target_square]

        castle_rights[0] = copy_castle[0]
        castle_rights[1] = copy_castle[1]
        castle_rights[2] = copy_castle[2]
        castle_rights[3] = copy_castle[3]
        ep = copy_ep

        if ply == 0:
            # fmt: off
            print_move_no_nl(move_list[move_index][MOVE_STARTING], move_list[move_index][MOVE_TARGET], move_list[move_index][MOVE_TAG])  # noqa: E501
            print(f": {nodes - prior_nodes}")
            # fmt: on

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
