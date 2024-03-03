import chess.pgn
import chess.pgn
import json

pgn_file = open("/PGNs/twic1525.pgn")
games = []

while True:
    game = chess.pgn.read_game(pgn_file)
    if game is None:
        break
    
    board = game.board()
    game_moves = []
    for move in game.mainline_moves():
        game_moves.append(board.san(move))
        board.push(move)
    
    uci_moves = [move.uci() for move in game_moves]
    
    games.append(uci_moves)

games_json = json.dumps(games)

print(games_json)
game = chess.pgn.read_game(pgn_file)

board = game.board()
moves = []
for move in game.mainline_moves():
    moves.append(board.san(move))
    board.push(move)

uci_moves = [move.uci() for move in moves]

print(uci_moves)
