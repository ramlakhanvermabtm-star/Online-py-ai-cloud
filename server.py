
from flask import Flask, request, jsonify
from engine import get_move
from trainer import train_game
import os

app = Flask(__name__)

SECRET = os.environ.get("PYTHON_SECRET", "")

def authorized():
    return (
        SECRET and
        request.headers.get("Authorization") == "Bearer " + SECRET
    )

@app.before_request
def protect():
    if not authorized():
        return jsonify({"error": "Unauthorized"}), 401

@app.get("/health")
def health():
    return jsonify({"status": "online"})

@app.post("/move")
def move():
    data = request.get_json(silent=True) or {}
    fen = data.get("fen")

    if not isinstance(fen, str) or len(fen) > 200:
        return jsonify({"error": "Invalid FEN"}), 400

    try:
        result = get_move(fen)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.post("/train")
def train():
    data = request.get_json(silent=True) or {}
    pgn = data.get("pgn")

    if not isinstance(pgn, str) or len(pgn) > 100000:
        return jsonify({"error": "Invalid PGN"}), 400

    try:
        result = train_game(pgn)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
