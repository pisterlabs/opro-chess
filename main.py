from Game import ChessGame
import json
import random
import pygame
import sys

if __name__ == "__main__":
  data = json.loads(open("PGNs/fens.json", "r").read())

  # initial prompt
  prompt = "Given a FEN string return the next best chess move in UCI format"

  total_games = 1

  for game_idx in range(total_games):
    fen = data["fens"][game_idx]
    game = ChessGame(fen)

    steps = 1
    batch = 100
    show_interval = 1000

    for step in range(steps):
      total_score = 0

      for idx in range(batch):
        # predict move with a LLM using prompt and board fen. Validate move, then play it
        move = random.choice(list(game.get_board().legal_moves)).uci()
        # print(move)

        # Show the board at these intervals, wait for input to continue
        if (idx+1) % show_interval == 0:
          game.play_move(move, show=True)

        # Play these moves quickly without showing the board
        else:
          game.play_move(move)

        total_score += game.get_score()

        game.get_board().pop()

      avg_score = total_score / batch

      # get new prompt from LLM using current prompt and avg score
      new_prompt = "Given a FEN string return the next best chess move in UCI format"

      print(f"Old Prompt: {prompt}")
      print(f"Average score: {avg_score}")
      print(f"New Prompt: {new_prompt}")
      print("--------------------\n")

      prompt = new_prompt

  print("done")
