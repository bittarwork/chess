#
# Web based GUI for BBC chess engine
#

# packages
from flask import Flask
from flask import render_template
from flask import request
import chess


# create chess engine instance

# create web app instance
app = Flask(__name__)

# root(index) route
@app.route('/')
def root():
    return render_template('bbc.html')

# make move API
@app.route('/make_move', methods=['POST'])
def make_move():
    # extract FEN string from HTTP POST request body
    fen = request.form.get('fen')
    # search for best move
    result = play(fen)
    board = chess.Board(result)
    fen = board.fen()
    return {'fen': fen}

def evaluate_board(board):
    # تحديد القيم لكل قطعة
    piece_values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0
    }
    score = 0
    # حساب ميزان المواد
    for square, piece in board.piece_map().items():
        value = piece_values[piece.piece_type]
        if piece.color == chess.WHITE:
            score += value
        else:
            score -= value
    # إضافة مكافآت/عقوبات استنادًا إلى مواقع القطع
    for square, piece in board.piece_map().items():
        if piece.color == chess.WHITE:
            if piece.piece_type == chess.PAWN:
                score += 10 + (7 - chess.square_distance(square, chess.E2))
            elif piece.piece_type == chess.KNIGHT:
                score += 30 + len(board.attacks(square))
            elif piece.piece_type == chess.BISHOP:
                score += 30 + len(board.attacks(square))
            elif piece.piece_type == chess.ROOK:
                score += 50 + len(board.attacks(square))
            elif piece.piece_type == chess.QUEEN:
                score += 90 + len(board.attacks(square))
            elif piece.piece_type == chess.KING:
                score += 900 + len(board.attacks(square))
        else:
            if piece.piece_type == chess.PAWN:
                score -= 10 + (chess.square_distance(square, chess.E7))
            elif piece.piece_type == chess.KNIGHT:
                score -= 30 + len(board.attacks(square))
            elif piece.piece_type == chess.BISHOP:
                score -= 30 + len(board.attacks(square))
            elif piece.piece_type == chess.ROOK:
                score -= 50 + len(board.attacks(square))
            elif piece.piece_type == chess.QUEEN:
                score -= 90 + len(board.attacks(square))
            elif piece.piece_type == chess.KING:
                score -= 900 + len(board.attacks(square))
    return score


# Define a transposition table to store board evaluations
transposition_table = {}

# Define a history table to store move history
history_table = {}

# Define the number of moves to consider in move ordering
k = 5

def play(board_fen):
    # Create a chess board object from the FEN notation
    board = chess.Board(board_fen)

    # Set the initial values
    depth = 2
    alpha = float('-inf')
    beta = float('inf')

    # Choose the first move as a random legal move
    move = list(board.legal_moves)[0]

    # Loop through the legal moves and evaluate them using alpha-beta with move ordering
    for legal_move in board.legal_moves:
        board.push(legal_move)

        # Use transposition table to retrieve previous evaluations
        if board.fen() in transposition_table:
            score = transposition_table[board.fen()]
        else:
            # Use history heuristic to order moves
            history_score = 0
            if board.fen() in history_table:
                history_score = history_table[board.fen()]
            score = alpha_beta_MinMaxbest(board, depth-1, alpha, beta, True, history_score)
            transposition_table[board.fen()] = score

        board.pop()

        # If the score is better than the current best score, update the best move and score
        if score > alpha:
            alpha = score
            move = legal_move

    # Make the selected move on the board
    board.push(move)

    # Update the history table with the selected move
    if board.fen() in history_table:
        history_table[board.fen()] += 1
    else:
        history_table[board.fen()] = 1

    # Return the FEN notation of the new board position after the selected move
    return board.fen()

def alpha_beta_MinMaxbest(board, l, alpha, beta, maximizing_player=True, history_score=0):
    # Check if the maximum depth has been reached or if the game is over
    if l == 0 or board.is_game_over():
        return evaluate_board(board)

    # Use transposition table to retrieve previous evaluations
    if board.fen() in transposition_table:
        return transposition_table[board.fen()]

    # Evaluate all legal moves and store them in a list with their scores
    moves_scores = []
    for move in board.legal_moves:
        board.push(move)

        # Use history heuristic to order moves
        history_move_score = 0
        if board.fen() in history_table:
            history_move_score = history_table[board.fen()]
        score = evaluate_board(board) + history_score + history_move_score
        moves_scores.append((move, score))
        board.pop()

    # Sort the list of moves based on their scores
    moves_scores.sort(key=lambda x: x[1], reverse=maximizing_player)

    # Select the top k moves to explore further
    moves_scores = moves_scores[:k]

    # Loop through the selected moves and evaluate them using alpha-beta
    for move, score in moves_scores:
        board.push(move)
        val = alpha_beta_MinMaxbest(board, l-1, alpha, beta, not maximizing_player, score - history_score)
        board.pop()

        # Update the best score and alpha/beta values
        if maximizing_player:
            alpha = max(alpha, val)
            if alpha >= beta:
                break
        else:
            beta = min(beta, val)
            if beta <= alpha:
                break

    # Use transposition table to store the board evaluation
    transposition_table[board.fen()] = alpha if maximizing_player else beta

    # Return the best score for the current player
    return alpha if maximizing_player else beta
if __name__ == '__main__':
    # start HTTP server
    app.run(debug=True, threaded=True)

