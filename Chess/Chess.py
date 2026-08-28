import copy
import pygame

pygame.init()

# Sizes
Window_Size = (800, 800)
Element_size = (100, 100)
screen = pygame.display.set_mode(Window_Size)
pygame.display.set_caption("Chess Game")

# Colors
Whitecolour = (235, 235, 208)
Blackcolour = (119, 148, 85)
CHECK_COLOR = (220, 60, 60)

alphabets = "abcdefgh"

# Global data structures
squares_Array = {}
piece_array = {}

Initial_Positions = {
    "Pawn": [(i, 2) for i in range(8)] + [(i, 7) for i in range(8)],
    "Rook": [(0, 1), (7, 1), (0, 8), (7, 8)],
    "Knight": [(1, 1), (6, 1), (1, 8), (6, 8)],
    "Bishop": [(2, 1), (5, 1), (2, 8), (5, 8)],
    "Queen": [(3, 1), (3, 8)],
    "King": [(4, 1), (4, 8)],
}


class Square:

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(self.x, self.y, Element_size[0], Element_size[1])

    def draw(self, screen, is_check=False):
        if is_check:
            color = CHECK_COLOR
        else:
            color = (
                Whitecolour
                if ((self.x // 100) + (self.y // 100)) % 2 == 0
                else Blackcolour
            )
        pygame.draw.rect(screen, color, self.rect)


class Pieces:

    def __init__(self, x: int, y: int, name: str, side: str):
        self.x = x
        self.y = y
        self.name = name
        self.side = side
        self.has_moved = False

        prefix = "w" if self.side == "White" else "b"
        try:
            self.image = pygame.image.load(f"ChessAssets/{prefix}_{self.name}.png")
        except pygame.error:
            self.image = pygame.Surface(Element_size, pygame.SRCALPHA)
            color = (255, 255, 255) if self.side == "White" else (30, 30, 30)
            pygame.draw.circle(self.image, color, (50, 50), 35)
            font = pygame.font.SysFont(None, 24)
            text = font.render(
                f"{prefix.upper()}_{self.name[0]}",
                True,
                (0, 0, 0) if self.side == "White" else (255, 255, 255),
            )
            self.image.blit(text, (30, 40))

        self.image = pygame.transform.scale(self.image, Element_size)


def starting_position():
    piece_array.clear()
    for piece, positions in Initial_Positions.items():
        for pos in positions:
            x, y = pos
            side = "Black" if y <= 2 else "White"
            p = Pieces(x, y, piece, side)
            piece_array[(p.x, p.y)] = p


def get_attacked_squares(enemy_side: str, board_state: dict) -> set:
    attacked = set()
    for p in board_state.values():
        if p.side != enemy_side:
            continue

        if p.name == "Pawn":
            dy = -1 if p.side == "White" else 1
            for dx in [-1, 1]:
                tx, ty = p.x + dx, p.y + dy
                if 0 <= tx <= 7 and 1 <= ty <= 8:
                    attacked.add((tx, ty))

        elif p.name == "Knight":
            for dx, dy in [
                (1, -2),
                (-1, -2),
                (2, -1),
                (-2, -1),
                (-2, 1),
                (2, 1),
                (1, 2),
                (-1, 2),
            ]:
                tx, ty = p.x + dx, p.y + dy
                if 0 <= tx <= 7 and 1 <= ty <= 8:
                    attacked.add((tx, ty))

        elif p.name == "King":
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    tx, ty = p.x + dx, p.y + dy
                    if 0 <= tx <= 7 and 1 <= ty <= 8:
                        attacked.add((tx, ty))

        elif p.name in ["Bishop", "Rook", "Queen"]:
            directions = []
            if p.name in ["Bishop", "Queen"]:
                directions.extend([(-1, -1), (-1, 1), (1, -1), (1, 1)])
            if p.name in ["Rook", "Queen"]:
                directions.extend([(-1, 0), (1, 0), (0, -1), (0, 1)])

            for dx, dy in directions:
                i, j = p.x + dx, p.y + dy
                while 0 <= i <= 7 and 1 <= j <= 8:
                    attacked.add((i, j))
                    if (i, j) in board_state:
                        break
                    i += dx
                    j += dy

    return attacked


def is_king_in_check(side: str, board_state: dict) -> bool:
    king_pos = None
    for p in board_state.values():
        if p.side == side and p.name == "King":
            king_pos = (p.x, p.y)
            break

    if king_pos is None:
        return False

    enemy_side = "Black" if side == "White" else "White"
    return king_pos in get_attacked_squares(enemy_side, board_state)


def get_pseudo_legal_moves(
    piece: Pieces, board_state: dict, last_double_pawn: tuple
) -> list:
    x, y = piece.x, piece.y
    side = piece.side
    legal = []

    if piece.name == "Pawn":
        dy = -1 if side == "White" else 1

        if 1 <= y + dy <= 8 and (x, y + dy) not in board_state:
            legal.append((x, y + dy))
            init_rank = 7 if side == "White" else 2
            if y == init_rank and (x, y + 2 * dy) not in board_state:
                legal.append((x, y + 2 * dy))

        for dx in [-1, 1]:
            tx, ty = x + dx, y + dy
            if 0 <= tx <= 7 and 1 <= ty <= 8:
                target = board_state.get((tx, ty))
                if target and target.side != side:
                    legal.append((tx, ty))

        if last_double_pawn is not None:
            ep_x, ep_y = last_double_pawn
            if y == ep_y and abs(x - ep_x) == 1:
                legal.append((ep_x, y + dy))

    elif piece.name == "Knight":
        offsets = [
            (1, -2),
            (-1, -2),
            (2, -1),
            (-2, -1),
            (-2, 1),
            (2, 1),
            (1, 2),
            (-1, 2),
        ]
        for dx, dy in offsets:
            tx, ty = x + dx, y + dy
            if 0 <= tx <= 7 and 1 <= ty <= 8:
                target = board_state.get((tx, ty))
                if target is None or target.side != side:
                    legal.append((tx, ty))

    elif piece.name in ["Bishop", "Rook", "Queen"]:
        directions = []
        if piece.name in ["Bishop", "Queen"]:
            directions.extend([(-1, -1), (-1, 1), (1, -1), (1, 1)])
        if piece.name in ["Rook", "Queen"]:
            directions.extend([(-1, 0), (1, 0), (0, -1), (0, 1)])

        for dx, dy in directions:
            i, j = x + dx, y + dy
            while 0 <= i <= 7 and 1 <= j <= 8:
                target = board_state.get((i, j))
                if target is None:
                    legal.append((i, j))
                else:
                    if target.side != side:
                        legal.append((i, j))
                    break
                i += dx
                j += dy

    elif piece.name == "King":
        offsets = [
            (-1, -1),
            (0, -1),
            (1, -1),
            (-1, 0),
            (1, 0),
            (-1, 1),
            (0, 1),
            (1, 1),
        ]
        for dx, dy in offsets:
            tx, ty = x + dx, y + dy
            if 0 <= tx <= 7 and 1 <= ty <= 8:
                target = board_state.get((tx, ty))
                if target is None or target.side != side:
                    legal.append((tx, ty))

        if not piece.has_moved and not is_king_in_check(side, board_state):
            enemy_side = "Black" if side == "White" else "White"
            attacked_sqs = get_attacked_squares(enemy_side, board_state)

            rook_ks = board_state.get((7, y))
            if (
                rook_ks
                and rook_ks.name == "Rook"
                and not rook_ks.has_moved
                and (5, y) not in board_state
                and (6, y) not in board_state
                and (5, y) not in attacked_sqs
                and (6, y) not in attacked_sqs
            ):
                legal.append((6, y))

            rook_qs = board_state.get((0, y))
            if (
                rook_qs
                and rook_qs.name == "Rook"
                and not rook_qs.has_moved
                and (1, y) not in board_state
                and (2, y) not in board_state
                and (3, y) not in board_state
                and (2, y) not in attacked_sqs
                and (3, y) not in attacked_sqs
            ):
                legal.append((2, y))

    return legal


def get_strictly_legal_moves(
    piece: Pieces, board_state: dict, last_double_pawn: tuple
) -> list:
    pseudo_moves = get_pseudo_legal_moves(piece, board_state, last_double_pawn)
    strictly_legal = []

    for target_x, target_y in pseudo_moves:
        sim_board = copy.deepcopy(board_state)
        sim_piece = sim_board[(piece.x, piece.y)]

        del sim_board[(piece.x, piece.y)]

        if (
            piece.name == "Pawn"
            and target_x != piece.x
            and (target_x, target_y) not in board_state
        ):
            capture_y = piece.y
            if (target_x, capture_y) in sim_board:
                del sim_board[(target_x, capture_y)]

        if (target_x, target_y) in sim_board:
            del sim_board[(target_x, target_y)]

        sim_piece.x = target_x
        sim_piece.y = target_y
        sim_board[(target_x, target_y)] = sim_piece

        if not is_king_in_check(piece.side, sim_board):
            strictly_legal.append((target_x, target_y))

    return strictly_legal


def get_all_legal_moves_for_side(
    side: str, board_state: dict, last_double_pawn: tuple
) -> list:
    all_moves = []
    for p in list(board_state.values()):
        if p.side == side:
            moves = get_strictly_legal_moves(p, board_state, last_double_pawn)
            all_moves.extend(moves)
    return all_moves


# ==========================================
# DRAW RULE EVALUATORS & POSITION HASHING
# ==========================================


def get_board_hash(board_state: dict, active_turn: str, last_double_pawn: tuple) -> str:
    """Generates a unique string hash of the current board state for repetition checks."""
    pieces_str_list = []
    for pos in sorted(board_state.keys()):
        p = board_state[pos]
        pieces_str_list.append(f"{p.side[0]}_{p.name}_{p.x}_{p.y}_{p.has_moved}")

    pieces_str = ",".join(pieces_str_list)
    ep_str = f"{last_double_pawn[0]}_{last_double_pawn[1]}" if last_double_pawn else "None"
    return f"{pieces_str}|Turn:{active_turn}|EP:{ep_str}"


def is_insufficient_material(board_state: dict) -> bool:
    """Checks if remaining pieces on board are insufficient to force a checkmate."""
    pieces = list(board_state.values())
    if len(pieces) <= 2:
        return True  # K vs K

    if len(pieces) == 3:
        names = [p.name for p in pieces]
        if "Knight" in names or "Bishop" in names:
            return True  # K+N vs K or K+B vs K

    if len(pieces) == 4:
        white_pieces = [p for p in pieces if p.side == "White"]
        black_pieces = [p for p in pieces if p.side == "Black"]

        # K+B vs K+B (Check if Bishops are on same color squares)
        if len(white_pieces) == 2 and len(black_pieces) == 2:
            wb = next((p for p in white_pieces if p.name == "Bishop"), None)
            bb = next((p for p in black_pieces if p.name == "Bishop"), None)
            if wb and bb:
                wb_color = (wb.x + wb.y) % 2
                bb_color = (bb.x + bb.y) % 2
                if wb_color == bb_color:
                    return True

    return False


def main():
    running = True
    Selected_piece = None
    drag_pos = (0, 0)
    Move_count = 0
    halfmove_clock = 0  # Tracker for 50-move rule
    new_pos = []
    last_double_pawn = None
    game_over_msg = ""
    position_counts = {}

    clock = pygame.time.Clock()

    for x in range(8):
        for y in range(1, 9):
            squares_Array[f"{alphabets[x]}{y}"] = Square(x * 100, (y - 1) * 100)

    def reset_game():
        nonlocal Selected_piece, drag_pos, Move_count, halfmove_clock
        nonlocal new_pos, last_double_pawn, game_over_msg, position_counts
        Selected_piece = None
        drag_pos = (0, 0)
        Move_count = 0
        halfmove_clock = 0
        new_pos = []
        last_double_pawn = None
        game_over_msg = ""
        position_counts = {}
        starting_position()

        # Record initial position hash
        init_hash = get_board_hash(piece_array, "White", None)
        position_counts[init_hash] = 1

    reset_game()

    while running:
        clock.tick(60)
        current_turn = "White" if Move_count % 2 == 0 else "Black"

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # Press 'R' to reset match
                    reset_game()

            elif event.type == pygame.MOUSEMOTION:
                if Selected_piece is not None:
                    drag_pos = event.pos

            elif event.type == pygame.MOUSEBUTTONDOWN and not game_over_msg:
                if event.button == 1:
                    mouse_x, mouse_y = event.pos
                    grid_x = mouse_x // 100
                    grid_y = (mouse_y // 100) + 1

                    p = piece_array.get((grid_x, grid_y))
                    if p and p.side == current_turn:
                        Selected_piece = p
                        drag_pos = event.pos
                        new_pos = get_strictly_legal_moves(Selected_piece, piece_array, last_double_pawn)

            elif event.type == pygame.MOUSEBUTTONUP and not game_over_msg:
                if event.button == 1 and Selected_piece is not None:
                    mouse_x, mouse_y = event.pos
                    target_x = mouse_x // 100
                    target_y = (mouse_y // 100) + 1

                    if (target_x, target_y) in new_pos:
                        start_x, start_y = Selected_piece.x, Selected_piece.y
                        is_pawn_move = Selected_piece.name == "Pawn"
                        is_capture = False

                        del piece_array[(start_x, start_y)]

                        # En Passant Capture
                        if (is_pawn_move and target_x != start_x and (target_x, target_y) not in piece_array):
                            del piece_array[(target_x, start_y)]
                            is_capture = True

                        # Standard Capture
                        if (target_x, target_y) in piece_array:
                            del piece_array[(target_x, target_y)]
                            is_capture = True

                        # Castling Move
                        if Selected_piece.name == "King" and abs(target_x - start_x) == 2:
                            if target_x == 6:
                                rook = piece_array.pop((7, start_y))
                                rook.x = 5
                                rook.has_moved = True
                                piece_array[(5, start_y)] = rook
                            elif target_x == 2:
                                rook = piece_array.pop((0, start_y))
                                rook.x = 3
                                rook.has_moved = True
                                piece_array[(3, start_y)] = rook

                        # Move Execution
                        Selected_piece.x = target_x
                        Selected_piece.y = target_y
                        Selected_piece.has_moved = True

                        # Auto-Promotion
                        if is_pawn_move and (target_y == 1 or target_y == 8):
                            Selected_piece.name = "Queen"
                            prefix = "w" if Selected_piece.side == "White" else "b"
                            try:
                                Selected_piece.image = pygame.image.load(
                                    f"ChessAssets/{prefix}_Queen.png"
                                )
                                Selected_piece.image = pygame.transform.scale(
                                    Selected_piece.image, Element_size
                                )
                            except pygame.error:
                                pass

                        piece_array[(target_x, target_y)] = Selected_piece

                        # Update Double-Step Pawn tracking for En Passant
                        if is_pawn_move and abs(target_y - start_y) == 2:
                            last_double_pawn = (target_x, target_y)
                        else:
                            last_double_pawn = None

                        # Update 50-Move Clock
                        if is_pawn_move or is_capture:
                            halfmove_clock = 0
                        else:
                            halfmove_clock += 1

                        Move_count += 1
                        next_turn = "White" if Move_count % 2 == 0 else "Black"

                        # ==========================================
                        # GAME OVER & DRAW EVALUATION CHECKS
                        # ==========================================
                        next_legal_moves = get_all_legal_moves_for_side(
                            next_turn, piece_array, last_double_pawn
                        )

                        # 1. Checkmate & Stalemate
                        if len(next_legal_moves) == 0:
                            if is_king_in_check(next_turn, piece_array):
                                game_over_msg = f"CHECKMATE! {current_turn.upper()} WINS!"
                            else:
                                game_over_msg = "DRAW BY STALEMATE!"

                        # 2. Insufficient Material
                        elif is_insufficient_material(piece_array):
                            game_over_msg = "DRAW BY INSUFFICIENT MATERIAL!"

                        # 3. 50-Move Rule (100 halfmoves = 50 full moves)
                        elif halfmove_clock >= 100:
                            game_over_msg = "DRAW BY 50-MOVE RULE!"

                        # 4. Threefold Repetition
                        else:
                            b_hash = get_board_hash(piece_array, next_turn, last_double_pawn)
                            position_counts[b_hash] = position_counts.get(b_hash, 0) + 1
                            if position_counts[b_hash] >= 3:
                                game_over_msg = "DRAW BY THREEFOLD REPETITION!"

                    Selected_piece = None
                    new_pos = []

        # Render Loop
        screen.fill((0, 0, 0))

        white_in_check = is_king_in_check("White", piece_array)
        black_in_check = is_king_in_check("Black", piece_array)

        # Draw Board Squares
        for sqr in squares_Array.values():
            grid_x = sqr.x // 100
            grid_y = (sqr.y // 100) + 1
            p = piece_array.get((grid_x, grid_y))
            in_check = (
                p
                and p.name == "King"
                and (
                    (p.side == "White" and white_in_check)
                    or (p.side == "Black" and black_in_check)
                )
            )
            sqr.draw(screen, is_check=in_check)

        # Highlight Valid Moves
        for move in new_pos:
            hx, hy = move
            highlight_surface = pygame.Surface(Element_size, pygame.SRCALPHA)
            pygame.draw.circle(highlight_surface, (0, 0, 0, 60), (50, 50), 16)
            screen.blit(highlight_surface, (hx * 100, (hy - 1) * 100))

        # Draw Active Pieces
        for p in piece_array.values():
            if p != Selected_piece:
                screen.blit(p.image, (p.x * 100, (p.y - 1) * 100))

        # Render Dragged Piece
        if Selected_piece is not None:
            screen.blit(
                Selected_piece.image, (drag_pos[0] - 50, drag_pos[1] - 50)
            )

        # Display Game Over Overlay
        if game_over_msg:
            font = pygame.font.SysFont(None, 42)
            sub_font = pygame.font.SysFont(None, 28)

            overlay = font.render(game_over_msg, True, (255, 255, 255))
            restart_text = sub_font.render("Press 'R' to Restart", True, (200, 200, 200))

            rect = overlay.get_rect(center=(400, 380))
            sub_rect = restart_text.get_rect(center=(400, 425))

            bg_rect = rect.union(sub_rect).inflate(40, 30)
            pygame.draw.rect(screen, (0, 0, 0), bg_rect)
            pygame.draw.rect(screen, (255, 255, 255), bg_rect, 2)

            screen.blit(overlay, rect)
            screen.blit(restart_text, sub_rect)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()