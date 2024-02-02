from Game import ChessGame

if __name__ == "__main__":
  game = ChessGame()

  moves = ["e2e4", "e7e5"]

  for idx in range(len(moves)):
    # Show the board at these intervals, wait for input to continue
    if idx == 1:
      game.play_move(moves[idx], show=True)

    # Play these moves quickly without showing the board
    else:
      game.play_move(moves[idx])
