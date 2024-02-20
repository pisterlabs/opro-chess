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

    response = llm.generate(prompt=prompt)

    # print("move response: ", response[0].text)

    uci_pattern = r"\b[a-h][1-8][a-h][1-8][nbrq]?\b"
    uci_matches = re.findall(uci_pattern, response[0].text)

    if uci_matches:
        first_uci_match = uci_matches[0]
        return_uci = first_uci_match
    else:
        print("No UCI match found")

    return return_uci


def predict_move_openai(input_prompt, fen_string, llm, num):
    prompt = f"{input_prompt} {' fen string: '} {fen_string}"

    completion = llm.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompt},
        ],
        n=num,
    )

    responses = []

    for choice in completion.choices:
        responses.append(choice.message.content)

    # print("move responses: ", responses)

    uci_pattern = r"\b[a-h][1-8][a-h][1-8][nbrq]?\b"

    return_ucis = []

    for resp in responses:
        uci_matches = re.findall(uci_pattern, resp)

        if uci_matches:
            first_uci_match = uci_matches[0]
            return_ucis.append(first_uci_match)
        else:
            print("No UCI match found")

    return return_ucis


def get_prompt_openai(prompt_score_list, llm):
    prompt_list = ""

    for idx, prompts in enumerate(prompt_score_list[:-6:-1]):
        prompt_list += (
            "\nPrompt "
            + str(idx + 1)
            + ":\n"
            + prompts[0]
            + "\nScore: "
            + str(prompts[1])
            + "\n"
        )

    # https://arxiv.org/pdf/2309.03409.pdf
    prompt = f"""Your task is to generate a prompt that will achieve a higher score than the given prompts. A higher score means a better move prediction. Below are some prompts and the score the prompt achieved.
  {prompt_list}\nGenerate a prompt that will achieve a higher score than the given prompts. A higher score means a better move prediction. the prompt should begin with "Prompt:" and should not include anything else.
  """

    # print(prompt)

    completion = llm.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompt},
        ],
    )

    response = completion.choices[0].message.content
    return_str = [x for x in response.split(":")[::-1] if len(x) > 4][0]

    # print("new prompt response: ", return_str)

    return return_str


if __name__ == "__main__":
    data = json.loads(open("PGNs/fens.json", "r").read())

    cohere_llm, openai_llm = init_llm()

    # prompt list, only include recent 5 prompts and scores
    prompt_score_list = []

    # initial prompt
    prompt = "Given a FEN string and legal moves, only return the next best move among the given moves in UCI format and nothing else. "

    show_interval = 1000
    steps = 2
    total_games = 2
    batch = 2
    num = 5

    for step in range(steps):
        original_prompt = prompt

        for game_idx in range(total_games):
            fen = data["fens"][game_idx]
            game = ChessGame(fen)

            print("fen:", game.get_board().fen())
            print()

            total_score = 0

            for idx in range(batch):
                # predict move with a LLM using prompt and board fen. Validate move, then play it

                prompt += "moves: " + " ".join(
                    [move.uci() for move in game.get_board().legal_moves]
                )

                # move = random.choice(list(game.get_board().legal_moves)).uci()
                # move = predict_move_cohere(prompt, fen, cohere_llm)
                moves = predict_move_openai(prompt, fen, openai_llm, num)

                for move in moves:
                    print("move:", move)

                    if not game.is_valid(move):
                        total_score += -10000000
                        continue

                    # Show the board at these intervals, wait for input to continue
                    if (idx + 1) % show_interval == 0:
                        game.play_move(move, show=True)

                    # Play these moves quickly without showing the board
                    else:
                        game.play_move(move)

                    total_score += game.get_score()

                    game.get_board().pop()

                prompt = original_prompt

        avg_score = total_score / (total_games * batch * num)

        # get new prompt from LLM using current prompt and avg score

        prompt_score_list.append([original_prompt, avg_score])

        if len(prompt_score_list) > 5:
            prompt_score_list = prompt_score_list[-5:]

        # new_prompt = "Given a FEN string return the next best chess move in UCI format"
        new_prompt = get_prompt_openai(prompt_score_list, openai_llm)

        print(f"Current Prompt: {original_prompt}")
        print(f"Average score: {avg_score}")
        print(f"New Prompt: {new_prompt}")
        print("--------------------\n")

        prompt = new_prompt

    print("done")
