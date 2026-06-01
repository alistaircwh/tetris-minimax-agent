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

    def early_game_compute_score(self, board: dict[Coord, PlayerColor]) -> float:
        """
        Evaluate board state for the early game (turns < 45).

        Scores each player as sum of min(6, pieces_in_row/col) across all rows and
        columns, plus a spread bonus for distinct rows/cols occupied. Returns
        my_score - 1.25 * opponent_score to encourage aggression.
        """
        my_score, opponent_score = 0, 0

        row_counts_my = [0] * BOARD_N
        row_counts_op = [0] * BOARD_N
        col_counts_my = [0] * BOARD_N
        col_counts_op = [0] * BOARD_N

        unique_rows_my, unique_cols_my = set(), set()
        unique_rows_op, unique_cols_op = set(), set()

        spread_bonus = 0.4

        for r in range(BOARD_N):
            for c in range(BOARD_N):
                if board.get(Coord(r, c)) == self._color:
                    row_counts_my[r] += 1
                    col_counts_my[c] += 1
                    unique_rows_my.add(r)
                    unique_cols_my.add(c)
                elif board.get(Coord(r, c)) == self.opponent_color:
                    row_counts_op[r] += 1
                    col_counts_op[c] += 1
                    unique_rows_op.add(r)
                    unique_cols_op.add(c)

        my_score = (sum(min(6, row_counts_my[r]) for r in range(BOARD_N)) +
                    sum(min(6, col_counts_my[c]) for c in range(BOARD_N)))
        opponent_score = (sum(min(6, row_counts_op[r]) for r in range(BOARD_N)) +
                    sum(min(6, col_counts_op[c]) for c in range(BOARD_N)))

        my_score += spread_bonus * (len(unique_rows_my) + len(unique_cols_my))

        return my_score - 1.25 * opponent_score

    def late_game_compute_score(self, board: dict[Coord, PlayerColor]) -> float:
        """
        Evaluate board state for the late game (turns >= 45).

        Same row/column scoring as early_game_compute_score but with a higher
        opponent weight (1.5x) and a mobility bonus: if the agent has more than
        25 available expansion directions, +20 is added to reward flexibility
        when the board is congested.
        """
        my_score, opponent_score = 0, 0

        row_counts_my = [0] * BOARD_N
        row_counts_op = [0] * BOARD_N
        col_counts_my = [0] * BOARD_N
        col_counts_op = [0] * BOARD_N

        unique_rows_my, unique_cols_my = set(), set()
        unique_rows_op, unique_cols_op = set(), set()

        spread_bonus = 0.5
        my_mobility = self.mobility(board, self._color)

        for r in range(BOARD_N):
            for c in range(BOARD_N):
                if board.get(Coord(r, c)) == self._color:
                    row_counts_my[r] += 1
                    col_counts_my[c] += 1
                    unique_rows_my.add(r)
                    unique_cols_my.add(c)
                elif board.get(Coord(r, c)) == self.opponent_color:
                    row_counts_op[r] += 1
                    col_counts_op[c] += 1
                    unique_rows_op.add(r)
                    unique_cols_op.add(c)

        my_score = (sum(min(6, row_counts_my[r]) for r in range(BOARD_N)) +
                    sum(min(6, col_counts_my[c]) for c in range(BOARD_N)))
        opponent_score = (sum(min(6, row_counts_op[r]) for r in range(BOARD_N)) +
                    sum(min(6, col_counts_op[c]) for c in range(BOARD_N)))

        my_score += spread_bonus * (len(unique_rows_my) + len(unique_cols_my))

        score = my_score - 1.5 * opponent_score

        if my_mobility > 25:
            score += 20

        return score

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

    def mobility(self, board: dict[Coord, PlayerColor], color: PlayerColor) -> int:
        """
        Count the number of expansion directions with at least one legal move.

        For each piece of the given color, checks each of the four adjacent
        directions. Increments by 1 if any legal placement exists in that
        direction (at most once per direction per piece).
        """
        mobility = 0

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
                            mobility += 1
                            break

        return mobility

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

        # Clear rows and columns sequentially to allow simultaneous clearing
        for r in rows_to_clear:
            for c in range(BOARD_N):
                cleared_info[Coord(r, c)] = board.get(Coord(r, c))
                board[Coord(r, c)] = None

        for c in columns_to_clear:
            for r in range(BOARD_N):
                # Avoid double-clearing cells already cleared by row pass
                if Coord(r, c) not in cleared_info:
                    cleared_info[Coord(r, c)] = board.get(Coord(r, c))
                    board[Coord(r, c)] = None

        return cleared_info

    def undo_clear_full_rows_and_columns(self, board: dict[Coord, PlayerColor], cleared_info: dict[Coord, PlayerColor]) -> None:
        """Restore cells previously removed by clear_full_rows_and_columns."""
        for coord, color in cleared_info.items():
            board[coord] = color

    def action(self, **referee: dict) -> Action:
        """
        This method is called by the referee each time it is the agent's turn
        to take an action. It must always return an action object.
        """

        opening_book = [
            PlaceAction(Coord(0, 9), Coord(0, 10), Coord(1, 9), Coord(1, 10)),
            PlaceAction(Coord(1, 8), Coord(1, 9), Coord(2, 8), Coord(2, 9)),
            PlaceAction(Coord(1, 1), Coord(1, 2), Coord(2, 1), Coord(2, 2)),
            PlaceAction(Coord(8, 1), Coord(9, 1), Coord(8, 2), Coord(9, 2)),
            PlaceAction(Coord(9, 9), Coord(8, 8), Coord(8, 9), Coord(9, 8)),
            PlaceAction(Coord(5, 5), Coord(5, 6), Coord(6, 5), Coord(6, 6)),
        ]

        if (self.turn_counter == 1) or (self.turn_counter == 2):
            for move in opening_book:
                if self.is_legal_placement(self.board, move):
                    return move

        elif self.turn_counter < 45:
            best_move = None
            max_eval = float('-inf')

            for move in self.generate_legal_moves(self.board, self._color):
                self.apply_move(self.board, move, self._color)
                cleared_info = self.clear_full_rows_and_columns(self.board)
                eval = self.early_game_compute_score(self.board)
                self.undo_clear_full_rows_and_columns(self.board, cleared_info)
                self.undo_apply_move(self.board, move, self._color)

                if eval > max_eval:
                    max_eval = eval
                    best_move = move

        else:
            best_move = None
            max_eval = float('-inf')

            for move in self.generate_legal_moves(self.board, self._color):
                self.apply_move(self.board, move, self._color)
                cleared_info = self.clear_full_rows_and_columns(self.board)
                eval = self.late_game_compute_score(self.board)
                self.undo_clear_full_rows_and_columns(self.board, cleared_info)
                self.undo_apply_move(self.board, move, self._color)

                if eval > max_eval:
                    max_eval = eval
                    best_move = move

        return best_move

    def update(self, color: PlayerColor, action: Action, **referee: dict) -> None:
        """
        This method is called by the referee after an agent has taken their
        turn. You should use it to update the agent's internal game state.
        """
        self.turn_counter += 1
        self.apply_move(self.board, action, color)
        self.clear_full_rows_and_columns(self.board)
