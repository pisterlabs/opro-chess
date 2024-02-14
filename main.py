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

  # print("move response: ", response[0].text)

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

  # print("move response: ", response)

  uci_pattern = r"\b[a-h][1-8][a-h][1-8][nbrq]?\b"
  uci_matches = re.findall(uci_pattern, response)

  if uci_matches:
    first_uci_match = uci_matches[0]
    return_uci = first_uci_match
  else:
    print("No UCI match found")

  return return_uci

def get_prompt_openai(current_prompt, avg_score, llm):
  return_str = current_prompt
  
  prompt = f"Original prompt: ' {current_prompt} ' Score: {avg_score}. The given prompt predicts the best chess move given a chess board. It's score is given. suggest just an alternative prompt without scores or moves in the format of \"Proposed prompt: \" that will achieve a higher score." 

  completion = llm.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
      {"role": "system", "content": prompt},
    ]
  )

  response = completion.choices[0].message.content
  return_str = [x for x in response.split('"')[::-1] if len(x) > 0][0]

  # print("new prompt response: ", return_str)

  return return_str

if __name__ == "__main__":
  data = json.loads(open("PGNs/fens.json", "r").read())

  cohere_llm, openai_llm = init_llm()

  # initial prompt
  prompt = "Given a FEN string and legal moves, only return the next best move among the given moves in UCI format and nothing else. "

  total_games = 1

  for game_idx in range(total_games):
    fen = data["fens"][game_idx]
    game = ChessGame(fen)

    steps = 2
    batch = 5
    show_interval = 1000

    print("fen:", game.get_board().fen())
    print()

    for step in range(steps):
      total_score = 0

      original_prompt = prompt

      for idx in range(batch):
        # predict move with a LLM using prompt and board fen. Validate move, then play it

        prompt += "moves: " + " ".join([move.uci() for move in game.get_board().legal_moves])

        # move = random.choice(list(game.get_board().legal_moves)).uci()
        # move = predict_move_cohere(prompt, fen, cohere_llm)
        move = predict_move_openai(prompt, fen, openai_llm)
        
        print("move:", move)

        if not game.is_valid(move):
          total_score += -10000000
          continue

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

      # new_prompt = "Given a FEN string return the next best chess move in UCI format"
      new_prompt = get_prompt_openai(original_prompt, avg_score, openai_llm)

      print(f"Current Prompt: {original_prompt}")
      print(f"Average score: {avg_score}")
      print(f"New Prompt: {new_prompt}")
      print("--------------------\n")

      prompt = new_prompt

  print("done")
