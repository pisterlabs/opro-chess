from chessboard import display
import chess

class ChessGame:
  def __init__(self) -> None:
    self.board = chess.Board()

  def get_board(self) -> chess.Board:
    return self.board

  def play_move(self, move_uci, show=False) -> None:
    display.pygame.quit()

    move = chess.Move.from_uci(move_uci)

    if move in self.board.legal_moves:
      self.board.push(move)
      
      if show:
        display.start(self.board.fen())

        while True:
          done = False

          for event in display.pygame.event.get():
            if event.type == display.pygame.KEYDOWN and event.key == display.pygame.K_RIGHT:
              done = True
              break

          if done:
            break
    else:
      print("invalid move: ", move.uci())
