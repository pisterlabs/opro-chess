from Game import ChessGame, Blackjack
import json
import os
import random
from dotenv import load_dotenv
import re
import cohere
from openai import OpenAI
import matplotlib.pyplot as plt


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


def predict_move_openai(input_prompt, moves_till_now, legal_moves, llm, num):
    prompt = f"{input_prompt} {'Moves played till now:'} {moves_till_now} {'Legal moves:'} {legal_moves}"

    # print(prompt)

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

def predict_move_openai_blackjack(input_prompt, player_dealer_info, llm):
    prompt = f"{input_prompt}\n{'Player and Dealer Card Info:'} {player_dealer_info} {'Legal moves: [hit, stand]'}"

    # print(prompt)

    completion = llm.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompt},
        ],
        n=1,
    )

    responses = []

    for choice in completion.choices:
        responses.append(choice.message.content)

    # print("move responses: ", responses)

    if "hit" in responses[0].lower():
        return "hit"
    else:    
        return "stand"

def get_prompt_openai(prompt_score_list, example_data, llm, game_name):
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
            "\nInfo till now: "
            + example[0]
            + "\nLegal moves: "
            + example[1]
            + "\nBest move: "
            + example[2]
            + "\n"
        )

    # https://arxiv.org/pdf/2309.03409.pdf
    prompt = f"""Your task is to generate a prompt that will achieve a higher score than the given prompts. A higher score means a better move prediction. Below are some prompts to play {game_name} and the score the prompt achieved.
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
    return_str = response.split("Prompt:")[-1].strip()

    # print("new prompt response: ", return_str)

    return return_str


if __name__ == "__main__":
    data = json.loads(open("PGNs/data.json", "r").read())

    cohere_llm, openai_llm = init_llm()

    # prompt list, only include recent 5 prompts and scores
    prompt_score_list = []

    # initial prompt
    # prompt = "Given the moves played till now and a list of legal moves, select and return only the next best move from the given list of legal moves in SAN format and nothing else."
    prompt = "Return the next best move for the player given the player's and dealer's card info and legal moves"

    show_interval = 1000
    steps = 15
    total_games = 5
    batch = 1
    num = 5

    xs = []
    ys = []

    example_data = []

    for step in range(steps):
        total_score = 0

        for game_idx in range(total_games):
            # fen = data["fens"][game_idx]
            # moves_till_now = data["moves"][game_idx] + "."

            # game = ChessGame(fen)

            # print("fen:", game.get_board().fen())
            # print()

            # legal_moves = (
            #     "["
            #     + ", ".join(
            #         [
            #             game.get_board().san(move)
            #             for move in game.get_board().legal_moves
            #         ]
            #     )
            #     + "]"
            # )

            for idx in range(batch):
                # predict move with an LLM. Validate move, then play it

                # move = random.choice(list(game.get_board().legal_moves)).uci()
                # move = predict_move_cohere(prompt, fen, cohere_llm)
                # moves = predict_move_openai(
                #     prompt, moves_till_now, legal_moves, openai_llm, num
                # )

                # for move in moves:
                #     print("move:", move)

                #     if not game.is_valid(move, san=True):
                #         total_score += -5000
                #         continue

                #     # Show the board at these intervals, wait for input to continue
                #     if (idx + 1) % show_interval == 0:
                #         game.play_move(move, show=True, san=True)

                #     # Play these moves quickly without showing the board
                #     else:
                #         game.play_move(move, san=True)

                #     total_score += game.get_score()

                #     game.get_board().pop()

                player = ("Player", 1000)
                game = Blackjack(player)
                table = game.get_table()
                dealer = table.dealer
                move_list = []
                
                for player in table: # singluar player
                    firstMove = True

                    while not (player.bust or player.stand):
                        # predict move with an LLM. Validate move, then play it
                        
                        move = predict_move_openai_blackjack(prompt, game.print_cards(dealer) + " " + game.print_cards(player), openai_llm)

                        # print("move:", move)
                        move_list.append(move)

                        # print("--- Info ---")
                        # print(game.print_cards(dealer) + " " + game.print_cards(player))
                        # print("--- End of Info ---")

                        if firstMove:
                            example_data.append([game.print_cards(dealer) + " " + game.print_cards(player), "[hit, stand]", move])

                        game.play_round(table, player, move)

                        firstMove = False

                # print("move list:", move_list)
                score = game.show_result(table)

                total_score += score

                if score < 0:
                    example_data.pop()

                # move = game.get_best_move()

            # best_move = game.get_best_move()
            # example_data.append([moves_till_now, legal_moves, best_move])

        avg_score = total_score / ((total_games * batch) * 1000)

        # get new prompt from LLM using prompt_score_list

        prompt_score_list.append([prompt, avg_score])

        prompt_score_list = prompt_score_list[-5:]

        example_data = example_data[-5:]

        # new_prompt = "Given a FEN string return the next best chess move in UCI format"
        new_prompt = get_prompt_openai(prompt_score_list, example_data, openai_llm, "Blackjack")

        # print(f"Current Prompt: {prompt}")
        # print(f"Average score: {avg_score}")
        # print(f"New Prompt: {new_prompt}")
        # print("--------------------\n")

        xs.append(step)
        ys.append(avg_score)

        print(f"Step: {step}")
        print(f"Average score: {avg_score}")
        print(f"Prompt: {prompt}")
        print("--------------------\n")
        print()

        prompt = new_prompt

    plt.plot(xs, ys)
    plt.show()

    print("done")
