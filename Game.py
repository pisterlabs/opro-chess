from chessboard import display
import chess
from chess.engine import Score
import random

class ChessGame:
  def __init__(self, starting_fen=None) -> None:
    self.engine = chess.engine.SimpleEngine.popen_uci(r"/opt/homebrew/bin/stockfish")

    if starting_fen:
      self.board = chess.Board(starting_fen)
    else:
      self.board = chess.Board()

  def get_board(self) -> chess.Board:
    return self.board
  
  def get_score(self) -> int:
    analyze_board = chess.Board(self.board.fen())
    info = self.engine.analyse(analyze_board, chess.engine.Limit(time=0.1))

    return info["score"].pov(not analyze_board.turn).score(mate_score=1000000)
  
  def is_valid(self, move_uci) -> bool:
    move = chess.Move.from_uci(move_uci)

    return move in self.board.legal_moves

  def play_move(self, move_uci, show=False) -> None:
    move = chess.Move.from_uci(move_uci)

    self.board.push(move)
      
    if show:
      display.start(self.board.fen())

      while True:
        for event in display.pygame.event.get():
          if event.type == display.pygame.KEYDOWN and event.key == display.pygame.K_RIGHT:
            display.pygame.quit()
            return
