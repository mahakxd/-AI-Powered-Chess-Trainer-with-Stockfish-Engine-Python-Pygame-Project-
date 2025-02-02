import chess
import chess.engine
import pygame
import sys

pygame.init()
pygame.mixer.init()

WINDOW_SIZE = 550
BOARD_SIZE = WINDOW_SIZE  
SQUARE_SIZE = BOARD_SIZE // 8 
INFO_BOX_HEIGHT = 100  
FPS = 30
FONT_SIZE = 14

WHITE = (240, 217, 181)
GREEN = (181, 136, 99)
BLACK = (0, 0, 0)
TEXT_COLOR = (255, 255, 255)
HIGHLIGHT_COLOR = (0, 255, 0, 100)

board = chess.Board()
STOCKFISH_PATH = "D:/stockfish/stockfish-windows-x86-64-sse41-popcnt.exe"
engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
engine.configure({'Skill Level': 20})

piece_images = {}
piece_symbols = {'p': 'pawn', 'n': 'knight', 'b': 'bishop', 'r': 'rook', 'q': 'queen', 'k': 'king'}
colors = ['white', 'black']

for color in colors:
    for symbol, name in piece_symbols.items():
        image_path = f"images/{color}_{name}.png"
        piece_images[f"{color}_{name}"] = pygame.transform.scale(pygame.image.load(image_path), (SQUARE_SIZE, SQUARE_SIZE))

move_sound = pygame.mixer.Sound("sounds/chess_move.mp3")
lose_sound = pygame.mixer.Sound("sounds/lose_laugh.wav")

screen = pygame.display.set_mode((WINDOW_SIZE, BOARD_SIZE + INFO_BOX_HEIGHT))
pygame.display.set_caption("Chess Trainer")
font = pygame.font.Font(None, 36)

def draw_board():
    for row in range(8):
        for col in range(8):
            color = GREEN if (row + col) % 2 == 0 else WHITE
            pygame.draw.rect(screen, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

            if col == 0:
                label = font.render(str(8 - row), True, BLACK)
                screen.blit(label, (5, row * SQUARE_SIZE))
            if row == 7:
                label = font.render(chr(97 + col), True, BLACK)
                screen.blit(label, (col * SQUARE_SIZE + SQUARE_SIZE - 20, BOARD_SIZE - 20))

def draw_pieces():
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            name = f"{'white' if piece.color == chess.WHITE else 'black'}_{piece_symbols[piece.symbol().lower()]}"
            row, col = divmod(square, 8)
            screen.blit(piece_images[name], (col * SQUARE_SIZE, row * SQUARE_SIZE))

def highlight_square(square, color):
    row, col = divmod(square, 8)
    surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
    pygame.draw.rect(surface, color, (0, 0, SQUARE_SIZE, SQUARE_SIZE))
    screen.blit(surface, (col * SQUARE_SIZE, row * SQUARE_SIZE))

def evaluate_move(move):
    info = engine.analyse(board, chess.engine.Limit(depth=18)) 
    best_move = info.get("pv")[0] if info.get("pv") else None
    
    if move == best_move:
        return "Excellent move! You played the best move."
    else:
        board.push(move)
        score = engine.analyse(board, chess.engine.Limit(depth=18))["score"].relative.score()
        board.pop()
        return f"Best move: {best_move}. Your move: {move}. Score: {score}" if score else "Try a different move."

def draw_review_box(review_text):
    review_box_surface = pygame.Surface((WINDOW_SIZE, INFO_BOX_HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(review_box_surface, (50, 50, 50, 150), (10, 10, WINDOW_SIZE - 20, INFO_BOX_HEIGHT - 20), border_radius=15)
    pygame.draw.rect(review_box_surface, (0, 0, 0, 100), (12, 12, WINDOW_SIZE - 24, INFO_BOX_HEIGHT - 24), border_radius=15)
    screen.blit(review_box_surface, (0, BOARD_SIZE))
    text_surface = font.render(review_text, True, TEXT_COLOR)
    screen.blit(text_surface, (20, BOARD_SIZE + 35))

def prompt_rematch():
    rematch_font = pygame.font.Font(None, 36)
    text_surface = rematch_font.render("Game Over! Press 'R' for rematch or 'Q' to quit.", True, (255, 255, 0))
    screen.blit(text_surface, (BOARD_SIZE // 2 - text_surface.get_width() // 2, BOARD_SIZE // 2 - text_surface.get_height() // 2))
    pygame.display.flip()

def get_legal_moves():
    legal_moves = list(board.legal_moves)
    if len(legal_moves) == 0:
        return None  
    return legal_moves

def main():
    clock = pygame.time.Clock()
    selected_square = None
    valid_moves = []
    review_text = "Welcome to Chess Trainer!"
    move_times = []
    move_count = 0

    while not board.is_game_over():
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                engine.quit()
                return

            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if y < BOARD_SIZE:
                    col, row = x // SQUARE_SIZE, y // SQUARE_SIZE
                    square = row * 8 + col

                    if selected_square is None:
                        piece = board.piece_at(square)
                        if piece and piece.color == board.turn:
                            selected_square = square
                            valid_moves = [move for move in board.legal_moves if move.from_square == square]
                    else:
                        move = chess.Move(selected_square, square)

                        if move in valid_moves:
                            move_count += 1
                            start_time = pygame.time.get_ticks()

                            review_text = evaluate_move(move)
                            board.push(move)

                            move_sound.play()

                            if not board.is_game_over():
                                result = engine.play(board, chess.engine.Limit(depth=18))
                                board.push(result.move)
                                review_text += f" | AI played: {result.move}"

                            end_time = pygame.time.get_ticks()
                            move_time = end_time - start_time
                            move_times.append(move_time)

                        selected_square = None
                        valid_moves = []

        draw_board()
        if selected_square is not None:
            highlight_square(selected_square, HIGHLIGHT_COLOR)
            for move in valid_moves:
                highlight_square(move.to_square, HIGHLIGHT_COLOR)
        draw_pieces()
        draw_review_box(review_text)

        pygame.display.flip()

    if board.is_checkmate():
        lose_sound.play()

    avg_time = sum(move_times) / len(move_times) if move_times else 0
    avg_accuracy = (move_count / len(board.move_stack)) * 100 if len(board.move_stack) > 0 else 0
    print("Game Over!")
    print("Result:", board.result())
    print(f"Average time per move: {avg_time:.2f} ms")
    print(f"Average accuracy: {avg_accuracy:.2f}%")

    prompt_rematch()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                engine.quit()
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    board.reset()
                    main()
                if event.key == pygame.K_q:
                    pygame.quit()
                    engine.quit()
                    sys.exit()

if __name__ == "__main__":
    main()
