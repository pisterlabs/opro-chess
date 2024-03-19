from chessboard import display
import chess
from chess.engine import Score
import random


class ChessGame:
    def __init__(self, starting_fen=None) -> None:
        self.engine = chess.engine.SimpleEngine.popen_uci(
            r"/usr/games/stockfish"
        )

        if starting_fen:
            self.board = chess.Board(starting_fen)
        else:
            self.board = chess.Board()

    def get_board(self) -> chess.Board:
        return self.board

    def get_score(self) -> int:
        analyze_board = chess.Board(self.board.fen())
        info = self.engine.analyse(analyze_board, chess.engine.Limit(time=1))

        return info["score"].pov(not analyze_board.turn).score(mate_score=5000)
    
    def get_best_move(self) -> str:
        analyze_board = chess.Board(self.board.fen())
        result = self.engine.play(analyze_board, chess.engine.Limit(time=1))

        return self.board.san(result.move)

    def is_valid(self, move_str, san=False) -> bool:
        if san:
            try:
                move = self.board.parse_san(move_str)
            except:
                return False
        else:
            move = chess.Move.from_uci(move_str)

        return move in self.board.legal_moves

    def play_move(self, move_str, show=False, san=False) -> None:
        if san:
            move = self.board.parse_san(move_str)
        else:
            move = chess.Move.from_uci(move_str)

        self.board.push(move)

        if show:
            display.start(self.board.fen())

            while True:
                for event in display.pygame.event.get():
                    if (
                        event.type == display.pygame.KEYDOWN
                        and event.key == display.pygame.K_RIGHT
                    ):
                        display.pygame.quit()
                        return
    
    def set_board_to_fen(self, new_fen: str) -> None:
        """Sets the board to a new position specified by a FEN string."""
        self.board.set_fen(new_fen)

    def close(self) -> None:
        self.engine.quit()