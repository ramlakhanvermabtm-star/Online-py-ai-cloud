
import chess
import chess.pgn
import json
import os
from io import StringIO

MODEL_FILE = "model.json"
GAMES_FILE = "games.jsonl"

def load_model():
    try:
        with open(MODEL_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_model(model):
    temporary = MODEL_FILE + ".tmp"

    with open(temporary, "w") as f:
        json.dump(model, f)

    os.replace(temporary, MODEL_FILE)

def train_game(pgn_text):
    game = chess.pgn.read_game(StringIO(pgn_text))

    if game is None or game.errors:
        raise ValueError("Invalid PGN")

    result = game.headers.get("Result", "*")

    if result not in ("1-0", "0-1", "1/2-1/2"):
        raise ValueError("Game is not completed")

    if not list(game.mainline_moves()):
        raise ValueError("Empty game")

    model = load_model()
    board = game.board()
    updated = 0

    for move in game.mainline_moves():
        key = " ".join(board.fen().split()[:4])

        if result == "1-0" and board.turn == chess.WHITE:
            reward = 1
        elif result == "0-1" and board.turn == chess.BLACK:
            reward = 1
        else:
            reward = 0

        if reward:
            position = model.setdefault(key, {})
            position[move.uci()] = min(
                20,
                position.get(move.uci(), 0) + reward
            )
            updated += 1

        board.push(move)

    save_model(model)

    with open(GAMES_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "result": result,
            "pgn": pgn_text
        }) + "\n")

    return {
        "status": "trained",
        "positions_updated": updated,
        "model_positions": len(model)
    }
