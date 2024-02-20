import io
import json
import chess.pgn

full_pgn = open("PGNs/twic1525.pgn").read()
split_pgns = full_pgn.split("\n\n")

pgns = []

for idx in range(1, len(split_pgns), 2):
    pgns.append(split_pgns[idx - 1] + "\n" + split_pgns[idx])

data = {"fens": []}

for pgn in pgns:
    game = chess.pgn.read_game(io.StringIO(pgn))
    board = game.board()

    idx = 0
    for move in game.mainline_moves():
        board.push(move)

        if idx >= 10:
            data["fens"].append(board.fen())

        idx += 1

with open("PGNs/fens.json", "w") as f:
    f.write(json.dumps(data, indent=2))
