# COMP30024 Artificial Intelligence, Semester 1 2024
# Project Part B: Game Playing Agent

from referee.game import PlayerColor, Action, PlaceAction, Coord, BOARD_N
from referee.game.coord import Vector2
from .templates import precomputed_moves


class Agent:
    """
    This class is the "entry point" for your agent, providing an interface to
    respond to various Tetress game events.
    """

    def __init__(self, color: PlayerColor, **referee: dict):
        """
        This constructor method runs when the referee instantiates the agent.
        Any setup and/or precomputation should be done here.
        """
        self._color = color
        self.board: dict[Coord, PlayerColor] = {}
        self.opponent_color = PlayerColor.BLUE if color == PlayerColor.RED else PlayerColor.RED
        self.turn_counter = 1

    def compute_score(self, board: dict[Coord, PlayerColor]) -> float:
        """
        Evaluate board state using row/column piece counts, spread, and central control.

        Scores each player as sum of min(5, pieces_in_row/col) across all rows and
        columns, plus bonuses for central 3x3 occupancy and spread (distinct rows/cols).
        Returns my_score - opponent_score.
        """
        my_score, opponent_score = 0, 0

        row_counts_my = [0] * BOARD_N
        row_counts_op = [0] * BOARD_N
        col_counts_my = [0] * BOARD_N
        col_counts_op = [0] * BOARD_N

        central_start, central_end = 4, 6
        central_control_bonus = 0.5
        spread_bonus = 0.4

        unique_rows_my, unique_cols_my = set(), set()
        unique_rows_op, unique_cols_op = set(), set()

        for r in range(BOARD_N):
            for c in range(BOARD_N):
                if board.get(Coord(r, c)) == self._color:
                    row_counts_my[r] += 1
                    col_counts_my[c] += 1
                    unique_rows_my.add(r)
                    unique_cols_my.add(c)
                    if central_start <= r <= central_end and central_start <= c <= central_end:
                        my_score += central_control_bonus
                elif board.get(Coord(r, c)) == self.opponent_color:
                    row_counts_op[r] += 1
                    col_counts_op[c] += 1
                    unique_rows_op.add(r)
                    unique_cols_op.add(c)
                    if central_start <= r <= central_end and central_start <= c <= central_end:
                        opponent_score += central_control_bonus

        my_score = (sum(min(5, row_counts_my[r]) for r in range(BOARD_N)) +
                    sum(min(5, col_counts_my[c]) for c in range(BOARD_N)))
        opponent_score = (sum(min(5, row_counts_op[r]) for r in range(BOARD_N)) +
                    sum(min(5, col_counts_op[c]) for c in range(BOARD_N)))

        my_score += spread_bonus * (len(unique_rows_my) + len(unique_cols_my))
        opponent_score += spread_bonus * (len(unique_rows_op) + len(unique_cols_op))

        return my_score - opponent_score

    def is_legal_placement(self, board: dict[Coord, PlayerColor], current_shape: PlaceAction) -> bool:
        """Return True if all four cells of current_shape are unoccupied."""
        for coord in current_shape.coords:
            if board.get(coord) is not None:
                return False
        return True

    def generate_legal_moves(self, board: dict[Coord, PlayerColor], color: PlayerColor) -> list[PlaceAction]:
        """
        Return all legal PlaceActions for the given color on the given board.

        For each piece of the given color, consults precomputed_moves[coord][direction]
        and skips any direction where the adjacent cell is occupied (pruning).
        """
        legal_moves = []

        adjacent_directions = {
            'up': Vector2(-1, 0),
            'right': Vector2(0, 1),
            'down': Vector2(1, 0),
            'left': Vector2(0, -1)
        }

        for coord, player_color in board.items():
            if player_color == color:
                possible_moves = precomputed_moves[coord]

                for direction, offset in adjacent_directions.items():
                    adjacent_coord = coord + offset

                    if board.get(adjacent_coord) is not None:
                        continue

                    for move in possible_moves[direction]:
                        if self.is_legal_placement(board, move):
                            legal_moves.append(move)

        return legal_moves

    def apply_move(self, board: dict[Coord, PlayerColor], move: PlaceAction, color: PlayerColor) -> None:
        """Place all four cells of move onto the board as the given color."""
        for coord in move.coords:
            board[coord] = color

    def undo_apply_move(self, board: dict[Coord, PlayerColor], move: PlaceAction, color: PlayerColor) -> None:
        """Remove all four cells of move from the board."""
        for coord in move.coords:
            del board[coord]

    def clear_full_rows_and_columns(self, board: dict[Coord, PlayerColor]) -> dict[Coord, PlayerColor]:
        """
        Clear any fully occupied rows and columns from the board in-place.

        Returns a cleared_info dict mapping each affected coordinate to its former
        color, which can be passed to undo_clear_full_rows_and_columns to reverse
        the operation.
        """
        rows_to_clear = []
        columns_to_clear = []
        cleared_info: dict[Coord, PlayerColor] = {}

        for r in range(BOARD_N):
            full_row = True
            for c in range(BOARD_N):
                if board.get(Coord(r, c)) is None:
                    full_row = False
                    break
            if full_row:
                rows_to_clear.append(r)

        for c in range(BOARD_N):
            full_column = True
            for r in range(BOARD_N):
                if board.get(Coord(r, c)) is None:
                    full_column = False
                    break
            if full_column:
                columns_to_clear.append(c)

        for r in rows_to_clear:
            for c in range(BOARD_N):
                cleared_info[Coord(r, c)] = board.get(Coord(r, c))
                board[Coord(r, c)] = None

        for c in columns_to_clear:
            for r in range(BOARD_N):
                if Coord(r, c) not in cleared_info:
                    cleared_info[Coord(r, c)] = board.get(Coord(r, c))
                    board[Coord(r, c)] = None

        return cleared_info

    def undo_clear_full_rows_and_columns(self, board: dict[Coord, PlayerColor], cleared_info: dict[Coord, PlayerColor]) -> None:
        """Restore cells previously removed by clear_full_rows_and_columns."""
        for coord, color in cleared_info.items():
            board[coord] = color

    def minimax(self, board: dict[Coord, PlayerColor], depth: int, alpha: float, beta: float, maximising: bool) -> tuple[float, PlaceAction | None]:
        """
        Minimax search with alpha-beta pruning.

        Returns (score, best_move). At depth 0 or terminal states (no legal moves),
        returns the static evaluation and None. Maximising=True means it's the
        agent's turn; False means the opponent's.
        """
        if maximising:
            current_color = self._color
        else:
            current_color = self.opponent_color

        if depth == 0 or not (moves := self.generate_legal_moves(board, current_color)):
            return self.compute_score(board), None

        if maximising:
            max_eval = float('-inf')
            best_move = None

            for move in moves:
                self.apply_move(board, move, current_color)
                cleared_info = self.clear_full_rows_and_columns(board)
                eval, _ = self.minimax(board, depth - 1, alpha, beta, False)
                self.undo_clear_full_rows_and_columns(board, cleared_info)
                self.undo_apply_move(board, move, current_color)

                if eval > max_eval:
                    max_eval = eval
                    best_move = move

                alpha = max(alpha, eval)
                if beta <= alpha:
                    break

            return max_eval, best_move

        else:
            min_eval = float('inf')
            best_move = None

            for move in moves:
                self.apply_move(board, move, current_color)
                cleared_info = self.clear_full_rows_and_columns(board)
                eval, _ = self.minimax(board, depth - 1, alpha, beta, True)
                self.undo_clear_full_rows_and_columns(board, cleared_info)
                self.undo_apply_move(board, move, current_color)

                if eval < min_eval:
                    min_eval = eval
                    best_move = move

                beta = min(beta, eval)
                if beta <= alpha:
                    break

            return min_eval, best_move

    def action(self, **referee: dict) -> Action:
        """
        This method is called by the referee each time it is the agent's turn
        to take an action. It must always return an action object.
        """

        if self.turn_counter == 1:
            return PlaceAction(Coord(3, 3), Coord(3, 4), Coord(4, 3), Coord(4, 4))

        if self.turn_counter == 2:
            return PlaceAction(Coord(2, 3), Coord(2, 4), Coord(2, 5), Coord(2, 6))

        elif self.turn_counter < 150:
            _, best_move = self.minimax(self.board, 1, float('-inf'), float('inf'), True)

        return best_move

    def update(self, color: PlayerColor, action: Action, **referee: dict) -> None:
        """
        This method is called by the referee after an agent has taken their
        turn. You should use it to update the agent's internal game state.
        """
        self.turn_counter += 1
        self.apply_move(self.board, action, color)
        self.clear_full_rows_and_columns(self.board)
