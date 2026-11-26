
import chess
import json
import os

MODEL_FILE = "model.json"

VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 335,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0
}

MATE = 100000

def load_model():
    try:
        with open(MODEL_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def position_key(board):
    return " ".join(board.fen().split()[:4])

def evaluate_white(board):
    score = 0

    for piece_type, value in VALUES.items():
        score += len(board.pieces(piece_type, chess.WHITE)) * value
        score -= len(board.pieces(piece_type, chess.BLACK)) * value

    # Basic center control
    center = [chess.D4, chess.E4, chess.D5, chess.E5]

    for square in center:
        piece = board.piece_at(square)

        if piece:
            bonus = 18
            score += bonus if piece.color == chess.WHITE else -bonus

    # Encourage minor-piece development
    for square in [chess.B1, chess.G1, chess.C1, chess.F1]:
        piece = board.piece_at(square)
        if piece and piece.color == chess.WHITE:
            score -= 12

    for square in [chess.B8, chess.G8, chess.C8, chess.F8]:
        piece = board.piece_at(square)
        if piece and piece.color == chess.BLACK:
            score += 12

    return score

def evaluate(board):
    score = evaluate_white(board)
    return score if board.turn == chess.WHITE else -score

def move_order_score(board, move):
    score = 0

    if board.is_capture(move):
        victim = board.piece_at(move.to_square)
        attacker = board.piece_at(move.from_square)

        if victim and attacker:
            score += 10 * VALUES.get(victim.piece_type, 0)
            score -= VALUES.get(attacker.piece_type, 0)

    if move.promotion:
        score += VALUES.get(move.promotion, 0)

    return score

def quiescence(board, alpha, beta, qdepth=3):
    stand = evaluate(board)

    if stand >= beta:
        return beta

    alpha = max(alpha, stand)

    if qdepth <= 0:
        return stand

    captures = list(board.generate_legal_captures())
    captures.sort(key=lambda m: move_order_score(board, m), reverse=True)

    for move in captures:
        board.push(move)
        score = -quiescence(board, -beta, -alpha, qdepth - 1)
        board.pop()

        if score >= beta:
            return beta

        alpha = max(alpha, score)

    return alpha

def search(board, depth, alpha, beta, model, ply=0):
    if board.is_checkmate():
        return -MATE + ply

    if board.is_game_over():
        return 0

    if depth <= 0:
        return quiescence(board, alpha, beta)

    key = position_key(board)
    preferences = model.get(key, {})

    moves = list(board.legal_moves)
    moves.sort(
        key=lambda m: (
            move_order_score(board, m) +
            preferences.get(m.uci(), 0)
        ),
        reverse=True
    )

    best = -float("inf")

    for move in moves:
        board.push(move)
        score = -search(
            board, depth - 1, -beta, -alpha, model, ply + 1
        )
        board.pop()

        score += preferences.get(move.uci(), 0)

        if score > best:
            best = score

        alpha = max(alpha, best)

        if alpha >= beta:
            break

    return best

def get_move(fen):
    board = chess.Board(fen)

    if not board.is_valid():
        raise ValueError("Invalid chess position")

    if board.is_game_over():
        raise ValueError("Game already ended")

    model = load_model()
    moves = list(board.legal_moves)

    if not moves:
        raise ValueError("No legal moves")

    moves.sort(key=lambda m: move_order_score(board, m), reverse=True)

    best_move = moves[0]
    best_score = -float("inf")

    # Depth 3 search
    for move in moves:
        board.push(move)
        score = -search(board, 2, -float("inf"), float("inf"), model)
        board.pop()

        score += model.get(position_key(board), {}).get(move.uci(), 0)

        if score > best_score:
            best_score = score
            best_move = move

    return {
        "move": best_move.uci(),
        "score": best_score
    }
