from Game import ChessGame
import json
import os
import random
from dotenv import load_dotenv
import re
import cohere
from openai import OpenAI
import google.generativeai as genai
import time
from tqdm import tqdm


def init_llm():
    load_dotenv()
    cohere_llm = cohere.Client(api_key=os.getenv("COHERE_API_KEY"))
    openai_llm = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    gemini_llm = genai.GenerativeModel(
        model_name="gemini-1.0-pro-latest",
        generation_config=genai.GenerationConfig(temperature=1, max_output_tokens=2048),
    )

    return cohere_llm, openai_llm, gemini_llm


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


def predict_move_openai(input_prompt, moves_till_now, legal_moves, llm, num):
    prompt = f"{input_prompt} {'Moves played till now:'} {moves_till_now} {'Legal moves:'} {legal_moves}"

    # print(prompt)

    completion = llm.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompt},
        ],
        n=num,
        temperature=1.0,
    )

    responses = []

    for choice in completion.choices:
        responses.append(choice.message.content)

    # print("move responses: ", responses)

    san_pattern = r"\b(?:[NBRQK]?[a-h]?[1-8]?x?[a-h][1-8][+#]?|O-O(?:-O)?|0-0(?:-0)?)\b"

    return_sans = []

    for resp in responses:
        san_matches = re.findall(san_pattern, resp)

        if san_matches:
            first_san_match = san_matches[0]
            return_sans.append(first_san_match)
        else:
            # print("No SAN match found")
            return_sans.append("0000")

    return return_sans


def get_prompt_openai(prompt_score_list, example_data, llm):
    prompt_list = ""
    examples = ""

    for idx, prompts in enumerate(prompt_score_list):
        prompt_list += (
            "\nPrompt "
            + str(idx + 1)
            + ":\n"
            + prompts[0]
            + "\nScore: "
            + str(prompts[1])
            + "\n"
        )

    for idx, example in enumerate(example_data):
        examples += (
            "\nMoves played till now: "
            + example[0]
            + "\nLegal moves: "
            + example[1]
            + "\nBest move: "
            + example[2]
            + "\n"
        )

    # https://arxiv.org/pdf/2309.03409.pdf
    prompt = f"""Your task is to generate a prompt that will achieve a higher score than the given prompts. A higher score means a better move prediction. Below are some prompts to play Chess and the score the prompt achieved.
  {prompt_list}\nBelow are some examples of the input and the best answer. \n{examples} \nGenerate a prompt that will achieve a higher score than the given prompts. A higher score means a better move prediction. the prompt should begin with "Prompt:" and should not include anything else.
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


def predict_move_gemini(input_prompt, moves_till_now, legal_moves, llm, num):
    prompt = f"{input_prompt} {'Moves played till now:'} {moves_till_now} {'Legal moves:'} {legal_moves}"

    # print(prompt)

    # Add num different responses. Model Temp = 1
    responses = set()
    while len(responses) < num:
        res = None
        while True:
            try:
                res = llm.generate_content(prompt).candidates[0].content.parts[0].text
                break
            except Exception as e:
                print(e)
                continue
        responses.add(res)

    # print("move responses: ", responses)

    san_pattern = r"\b(?:[NBRQK]?[a-h]?[1-8]?x?[a-h][1-8][+#]?|O-O(?:-O)?|0-0(?:-0)?)\b"

    return_sans = []

    for resp in responses:
        san_matches = re.findall(san_pattern, resp)

        if san_matches:
            first_san_match = san_matches[0]
            return_sans.append(first_san_match)
        else:
            # print("No SAN match found")
            return_sans.append("0000")

    return return_sans


def get_prompt_gemini(prompt_score_list, example_data, llm):
    prompt_list = ""
    examples = ""

    for idx, prompts in enumerate(prompt_score_list):
        prompt_list += (
            "\nPrompt "
            + str(idx + 1)
            + ":\n"
            + prompts[0]
            + "\nScore: "
            + str(prompts[1])
            + "\n"
        )

    for idx, example in enumerate(example_data):
        examples += (
            "\nMoves played till now: "
            + example[0]
            + "\nLegal moves: "
            + example[1]
            + "\nBest move: "
            + example[2]
            + "\n"
        )

    # https://arxiv.org/pdf/2309.03409.pdf
    prompt = f"""Your task is to generate a prompt that will achieve a higher score than the given prompts. A higher score means a better move prediction. Below are some prompts to play Chess and the score the prompt achieved.
  {prompt_list}\nBelow are some examples of the input and the best answer. \n{examples} \nGenerate a prompt that will achieve a higher score than the given prompts. A higher score means a better move prediction. the prompt should begin with "Prompt:" and should not include anything else.
  """

    # print(prompt)
    response = None
    while True:
        try:
            response = llm.generate_content(prompt).candidates[0].content.parts[0].text
            break
        except Exception as e:
            print(e)
            continue

    return_str = [x for x in response.split(":")[::-1] if len(x) > 4][0]

    # print("new prompt response: ", return_str)

    return return_str


def run(steps, total_games, num, llm, data, show_interval=1000, batch=1):
    # prompt list, only include recent 5 prompts and scores
    prompt_score_list = []

    # Output String to replace print statements
    output_str = ""

    # initial prompt
    prompt = "Given the moves played till now and a list of legal moves, select and return only the next best move from the given list of legal moves in SAN format and nothing else."

    for step in range(steps):
        example_data = []
        total_score = 0

        for game_idx in range(total_games):
            fen = data["fens"][game_idx]
            moves_till_now = data["moves"][game_idx] + "."

            # Loading game state from FEN
            game = ChessGame(fen)
            output_str += f"fen: {game.get_board().fen()}\n\n"

            legal_moves = (
                "["
                + ", ".join(
                    [
                        game.get_board().san(move)
                        for move in game.get_board().legal_moves
                    ]
                )
                + "]"
            )

            for idx in range(batch):
                # predict move with an LLM. Validate move, then play it

                # move = random.choice(list(game.get_board().legal_moves)).uci()
                # move = predict_move_cohere(prompt, fen, cohere_llm)
                moves = predict_move_gemini(
                    prompt, moves_till_now, legal_moves, llm, num
                )

                for move in moves:
                    output_str += f"move: {move}\n"

                    if not game.is_valid(move, san=True):
                        total_score += -5000
                        continue

                    # Show the board at these intervals, wait for input to continue
                    if (idx + 1) % show_interval == 0:
                        game.play_move(move, show=True, san=True)

                    # Play these moves quickly without showing the board
                    else:
                        game.play_move(move, san=True)

                    total_score += game.get_score()

                    game.get_board().pop()

            best_move = game.get_best_move()
            example_data.append([moves_till_now, legal_moves, best_move])
            game.close()
            print(f"{game_idx + 1}/{total_games} games. {step}/{steps} steps.")

        avg_score = total_score / (total_games * batch * num)

        # get new prompt from LLM using prompt_score_list

        prompt_score_list.append([prompt, avg_score])

        prompt_score_list = prompt_score_list[-5:]

        example_data = example_data[-5:]

        # new_prompt = "Given a FEN string return the next best chess move in UCI format"
        new_prompt = get_prompt_gemini(prompt_score_list, example_data, llm)

        output_str += f"Current Prompt: {prompt}\n"
        output_str += f"Average score: {avg_score}\n"
        output_str += f"New Prompt: {new_prompt}\n"
        output_str += "--------------------\n"

        prompt = new_prompt

    output_str += "done"
    return output_str, avg_score


if __name__ == "__main__":
    data = json.loads(open("PGNs/data.json", "r").read())

    cohere_llm, openai_llm, gemini_llm = init_llm()

    # Default Params
    show_interval = 1000
    batch = 1

    # Adjustable Params
    steps = 3
    total_games = 2
    num = 5

    # Run the game for prompts
    start_time = time.time()
    output_str, avg_score = run(steps, total_games, num, gemini_llm, data)  # batch = 1, show_interval = 1000 by default
    end_time = time.time()
    print(output_str, avg_score, end_time-start_time)
