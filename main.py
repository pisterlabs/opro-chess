from Game import ChessGame
import json
import os
import random
from dotenv import load_dotenv
import re
import cohere
from openai import OpenAI

def init_llm():
  load_dotenv()
  cohere_llm = cohere.Client(api_key=os.getenv("COHERE_API_KEY"))
  openai_llm = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

  return cohere_llm, openai_llm

def predict_move_cohere(input_prompt, fen_string, llm):
  return_uci = ""
  
  prompt = f"{input_prompt} {' fen string: '} {fen_string}"

  response = llm.generate(prompt = prompt)

  print("response text: ", response[0].text)

  uci_pattern = r"\b[a-h][1-8][a-h][1-8][nbrq]?\b"
  uci_matches = re.findall(uci_pattern, response[0].text)

  if uci_matches:
    first_uci_match = uci_matches[0]
    return_uci = first_uci_match
  else:
    print("No UCI match found")
  
  return return_uci

def predict_move_openai(input_prompt, fen_string, llm):
  return_uci = ""
  
  prompt = f"{input_prompt} {' fen string: '} {fen_string}"

  completion = llm.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
      {"role": "system", "content": prompt},
    ]
  )

  response = completion.choices[0].message.content

  print("response text: ", response)

  uci_pattern = r"\b[a-h][1-8][a-h][1-8][nbrq]?\b"
  uci_matches = re.findall(uci_pattern, response)

  if uci_matches:
    first_uci_match = uci_matches[0]
    return_uci = first_uci_match
  else:
    print("No UCI match found")

  return return_uci

if __name__ == "__main__":
  data = json.loads(open("PGNs/fens.json", "r").read())

  cohere_llm, openai_llm = init_llm()

  # initial prompt
  prompt = "Given a FEN string and legal moves, only return the next best move among the given moves in UCI format and nothing else. "

  total_games = 1

  for game_idx in range(total_games):
    fen = data["fens"][game_idx]
    game = ChessGame(fen)

    steps = 1
    batch = 1
    show_interval = 1000

    print("fen:", game.get_board().fen())

    for step in range(steps):
      total_score = 0

      for idx in range(batch):
        # predict move with a LLM using prompt and board fen. Validate move, then play it

        prompt += "moves: " + " ".join([move.uci() for move in game.get_board().legal_moves])

        # move = random.choice(list(game.get_board().legal_moves)).uci()
        # move = predict_move_cohere(prompt, fen, cohere_llm)
        move = predict_move_openai(prompt, fen, openai_llm)
        
        print("move:", move)

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
