from chessboard import display
import chess
import random

class ChessGame:
  def __init__(self, starting_fen=None) -> None:
    if starting_fen:
      self.board = chess.Board(starting_fen)
    else:
      self.board = chess.Board()

  def get_board(self) -> chess.Board:
    return self.board
  
  def get_score(self) -> int:
    return random.randint(-1, 1)

  # source: https://rosettacode.org/wiki/Generate_random_chess_position#Python
  @staticmethod
  def get_random_fen():
    board = [[" " for _ in range(8)] for _ in range(8)]
    piece_list = ["R", "N", "B", "Q", "P"]

    def place_kings(brd):
      while True:
        rank_white, file_white, rank_black, file_black = random.randint(0,7), random.randint(0,7), random.randint(0,7), random.randint(0,7)
        diff_list = [abs(rank_white - rank_black),  abs(file_white - file_black)]
        if sum(diff_list) > 2 or set(diff_list) == set([0, 2]):
          brd[rank_white][file_white], brd[rank_black][file_black] = "K", "k"
          break

    def populate_board(brd, wp, bp):
      for x in range(2):
        if x == 0:
          piece_amount = wp
          pieces = piece_list
        else:
          piece_amount = bp
          pieces = [s.lower() for s in piece_list]
        while piece_amount != 0:
          piece_rank, piece_file = random.randint(0, 7), random.randint(0, 7)
          piece = random.choice(pieces)
          if brd[piece_rank][piece_file] == " " and pawn_on_promotion_square(piece, piece_rank) == False:
            brd[piece_rank][piece_file] = piece
            piece_amount -= 1

    def fen_from_board(brd):
      fen = ""
      for x in brd:
        n = 0
        for y in x:
          if y == " ":
            n += 1
          else:
            if n != 0:
              fen += str(n)
            fen += y
            n = 0
        if n != 0:
          fen += str(n)
        fen += "/" if fen.count("/") < 7 else ""
      fen += " w - - 0 1\n"
      return fen

    def pawn_on_promotion_square(pc, pr):
      if pc == "P" and pr == 0:
        return True
      elif pc == "p" and pr == 7:
        return True
      return False

    piece_amount_white, piece_amount_black = random.randint(0, 15), random.randint(0, 15)
    place_kings(board)
    populate_board(board, piece_amount_white, piece_amount_black)

    return fen_from_board(board)

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
