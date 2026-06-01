# COMP30024 Artificial Intelligence, Semester 1 2024
# Project Part B: Game Playing Agent

from referee.game import PlayerColor, Action, PlaceAction, Coord, BOARD_N
from .templates import all_templates


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

    def compute_score(self, board: dict[Coord, PlayerColor]) -> int:
        """Return the piece-count difference: my pieces minus opponent's pieces."""
        my_score = sum(1 for color in board.values() if color == self._color)
        opponent_score = sum(1 for color in board.values() if color == self.opponent_color)
        return my_score - opponent_score

    def is_legal_placement(self, current_shape: PlaceAction) -> bool:
        """Return True if all four cells of current_shape are unoccupied on self.board."""
        for coord in current_shape.coords:
            if self.board.get(coord) is not None:
                return False
        return True

    def generate_legal_moves(self) -> list[PlaceAction]:
        """
        Return all legal PlaceActions for the agent's color on self.board.

        Iterates over the agent's own pieces and for each template direction checks
        whether the adjacent cell is empty before generating shapes (pruning).
        """
        legal_moves = []
        my_coords = [coord for coord, color in self.board.items() if color == self._color]

        for my_coord in my_coords:
            for template in all_templates:
                # Skip this direction if the adjacent cell is occupied
                check_coord = my_coord + (template[0]).v1
                if self.board.get(check_coord) is not None:
                    continue

                for shape in template:
                    current_shape = PlaceAction(
                        my_coord + shape.v1,
                        my_coord + shape.v2,
                        my_coord + shape.v3,
                        my_coord + shape.v4
                    )
                    if self.is_legal_placement(current_shape):
                        legal_moves.append(current_shape)

        return legal_moves

    def apply_move(self, board: dict[Coord, PlayerColor], move: PlaceAction, color: PlayerColor) -> None:
        """Place all four cells of move onto the board as the given color."""
        for coord in move.coords:
            board[coord] = color

    def clear_full_rows_and_columns(self, board: dict[Coord, PlayerColor]) -> None:
        """Clear any fully occupied rows and columns from the board in-place."""
        rows_to_clear = []
        columns_to_clear = []

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
                board[Coord(r, c)] = None

        for c in columns_to_clear:
            for r in range(BOARD_N):
                board[Coord(r, c)] = None

    def action(self, **referee: dict) -> Action:
        """
        This method is called by the referee each time it is the agent's turn
        to take an action. It must always return an action object.
        """

        if (self.turn_counter == 1) or (self.turn_counter == 2):
            match self._color:
                case PlayerColor.RED:
                    return PlaceAction(Coord(3, 3), Coord(3, 4), Coord(4, 3), Coord(4, 4))
                case PlayerColor.BLUE:
                    return PlaceAction(Coord(2, 3), Coord(2, 4), Coord(2, 5), Coord(2, 6))

        best_move = None
        best_score_diff = float('-inf')

        for move in self.generate_legal_moves():
            temp_board = self.board.copy()
            self.apply_move(temp_board, move, self._color)
            self.clear_full_rows_and_columns(temp_board)

            score_diff = self.compute_score(temp_board) - self.compute_score(self.board)

            if score_diff > best_score_diff:
                best_score_diff = score_diff
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
