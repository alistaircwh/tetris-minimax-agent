# COMP30024 Artificial Intelligence, Semester 1 2024
# Project Part A: Single Player Tetress

from .core import PlayerColor, Coord, PlaceAction, PriorityQueue
from .utils import render_board
from .templates import all_templates

import math

BOARD_N = 11

def goal_test(state: dict, target: 'Coord') -> bool:
    """Return True if the row or column containing target is fully occupied."""
    
    # Check if all coordinates horizontal to target are filled in.
    horizontal_filled = True
    for i in range(BOARD_N):
        if state.get(target.right(i)) is None:
            horizontal_filled = False
            break

    # Check if all coordinates vertical to target are filled in.
    vertical_filled = True
    for i in range(BOARD_N):
        if state.get(target.up(i)) is None:
            vertical_filled = False
            break
    
    # If either condition is true, goal state has been reached, return True
    return horizontal_filled or vertical_filled


def is_legal_placement(state: dict, current_shape: 'PlaceAction') -> bool:
    """Return True if all four cells of current_shape are unoccupied in state."""

    for coord in current_shape.coords:

        # If any coordinate of the shape is not empty, it is illegal to place there
        if state.get(coord) is not None:
            return False
        
    # All proposed placement coordinates are empty, so it is legal
    return True

def clear_full_rows_and_columns(state: dict, target: 'Coord') -> None:
    """
    Remove any fully occupied rows and columns from state in-place.

    Rows/columns containing the target coordinate are preserved — clearing them
    would remove the goal and make the puzzle unsolvable.
    """

    rows_to_clear = []
    columns_to_clear = []

    # Clear full rows
    for r in range(BOARD_N):
        full_row = True

        # Loops through the row to check if it is full, breaks if it is not full
        for c in range(BOARD_N):
            if state.get(Coord(r, c)) is None:
                full_row = False
                break

        # If row is full, and is not the goal state
        if full_row and r != target.r:
            rows_to_clear.append(r)


    # Clear full columns
    for c in range(BOARD_N):
        full_column = True

        # Loops through the column to check if it is full, breaks if it is not full
        for r in range(BOARD_N):
            if state.get(Coord(r, c)) is None:
                full_column = False
                break

        # If column is full, and is not the goal state
        if full_column and c != target.c:
            columns_to_clear.append(c)


    # Clear them subsequently to ensure simultaneous clearing is possible
    # Clears the entire row
    for r in rows_to_clear:
        for c in range(BOARD_N):
            state[Coord(r, c)] = None

    # Clears the entire column
    for c in columns_to_clear:
        for r in range(BOARD_N):
            state[Coord(r, c)] = None



def get_neighbours(state: dict, target: 'Coord') -> list[tuple[dict, 'PlaceAction']]:
    """
    Return all (new_state, action) pairs reachable from state in one placement.

    Generates every legal tetromino placement adjacent to an existing RED piece,
    applies the placement and any resulting line clears, and returns the resulting
    board state paired with the PlaceAction that produced it.
    """

    # Create empty lists
    neighbours = []
    red_coords = []

    # Fill list with the red coordinates to iterate over later
    for coord, color in state.items():
        if color == PlayerColor.RED:
            red_coords.append(coord)

    # Loop over red coordinates, to attempt placement of tetrinomos
    for red_coord in red_coords:

        # Loop through templates of all directions (up,right, down, left)
        for template in all_templates:

            # Pruning step: check if the coordinate directly adjacent is empty
            # Index at 0, because the first vector of the first shape represents the coordinate directly adjacent
            check_coord = red_coord + (template[0]).v1

            # Skip this template if check coordinate is not empty. No point attempting placements in that direction. 
            if state.get(check_coord) is not None:
                continue  

            # Loops through every shape/action
            for action in template:

                # Obtain current shape by summing the red coord and the action
                current_shape = PlaceAction(
                    red_coord + action.v1, 
                    red_coord + action.v2,
                    red_coord + action.v3,
                    red_coord + action.v4
                )

                # Returns true if placing shape is legal
                if is_legal_placement(state, current_shape):

                    # Since it is legal append new state along with information of what shape was placed. 
                    new_state = state.copy()
                    for coord in current_shape.coords:
                        new_state[coord] = PlayerColor.RED

                    # Check for and remove any potential lines (full row/columns)
                    clear_full_rows_and_columns(new_state, target)

                    # Do the appending
                    neighbours.append((new_state, current_shape))

    # Return list of possible neighbour nodes to explore
    return neighbours

def heuristic(state: dict, target: 'Coord') -> int:
    """
    Admissible heuristic: minimum moves to fill the target row or column.

    For each of the two possible goal lines (target row and target column), estimates
    the cost as ceil(distance_to_reach_line / 4) + ceil(empty_cells_in_line / 4).
    Distance uses modular arithmetic for the wrapping board. Returns the minimum
    of the two estimates.
    """
    empty_spaces_horizontal = 0
    empty_spaces_vertical = 0

    # Initialise the variables this way as the board wraps around
    minimum_row_distance = (BOARD_N//2)
    minimum_column_distance = (BOARD_N//2)
    

    # Calculate distance to reach the target's clearing row/column
    for coord, color in state.items():
        if color == PlayerColor.RED:
            distance_to_target_row = min(abs(coord.r - target.r), BOARD_N - abs(coord.r - target.r))
            distance_to_target_column = min(abs(coord.c - target.c), BOARD_N - abs(coord.c - target.c))

            minimum_row_distance = min(minimum_row_distance, distance_to_target_row)
            minimum_column_distance = min(minimum_column_distance, distance_to_target_column)


    # Count empty spaces horizontally and vertically
    for i in range(BOARD_N):
        if state.get(Coord(target.r, i)) is None:
            empty_spaces_horizontal += 1
        if state.get(Coord(i, target.c)) is None:
            empty_spaces_vertical += 1

    # Take the minimum between the estimated cost if the horizontal path is taken vs vertical path
    # Divide by 4, because 4 blocks in one shape
    # Round ups because there is no such thing as a fraction of a move.
    heuristic_value = min(math.ceil(minimum_row_distance /4) + math.ceil(empty_spaces_horizontal / 4),
        math.ceil(minimum_column_distance /4) + math.ceil(empty_spaces_vertical / 4))
    
    
    return heuristic_value

def reconstruct_path(came_from: dict, current) -> list['PlaceAction']:
    """Trace came_from back from current state to the start and return the action sequence."""
    total_path = []

    # Loop in a backward fashion to determine path taken
    while current in came_from:

        value = came_from[current]

        # Break once starting state is reached, which has a came_from value of None.
        if value is None:
            break

        previous, action = value
        total_path.append(action)
        current = previous

     # Reverse the path to get actions from start to goal
    return total_path[::-1] 

def board_to_tuple(board: dict) -> tuple:
    """Convert board dict to a hashable tuple-of-tuples for use as a dict key."""
    board_tuple = []
    for r in range(BOARD_N):
        row = []
        for c in range(BOARD_N):
            cell = board.get(Coord(r, c), None)
            row.append(cell)
        board_tuple.append(tuple(row))
    return tuple(board_tuple)

# Main A star search Algorithmn, takes in a starting board state, and a target. Outputs solution if one exists. 
def search(
    board: dict[Coord, PlayerColor], 
    target: Coord
) -> list[PlaceAction] | None:
    """
    This is the entry point for your submission. You should modify this
    function to solve the search problem discussed in the Part A specification.
    See `core.py` for information on the types being used here.

    Parameters:
        `board`: a dictionary representing the initial board state, mapping
            coordinates to "player colours". The keys are `Coord` instances,
            and the values are `PlayerColor` instances.  
        `target`: the target BLUE coordinate to remove from the board.
    
    Returns:
        A list of "place actions" as PlaceAction instances, or `None` if no
        solution is possible.
    """

    # Initialise PQ with starting board
    open_set = PriorityQueue()
    open_set.put(board, 0)

    # Dictionary, where each key is a node/state and its values stores its previous state and the action taken.
    came_from = {board_to_tuple(board): None}

    # Dictionary, where each key is a node/state and its value is the cheapest known cost to reach that state.
    g_score = {board_to_tuple(board): 0}

    # Loop goes on as long as the Priority Queue still has nodes left to explore.
    while not open_set.empty():

        # Get next highest priority node
        current_board = open_set.get()
        current_tuple = board_to_tuple(current_board)

        if goal_test(current_board, target):
            return reconstruct_path(came_from, current_tuple)

        # Look for all the neighbours of the current node/board/state
        for neighbour_board, action in get_neighbours(current_board, target):

            neighbour_tuple = board_to_tuple(neighbour_board) # tuple of tuples representation

            # The distance from start to current neighbour state
            current_g_score = g_score[current_tuple] + 1  # One move more than previous state

            # If This state has not been reached before, or at least not at this lower cost.
            if neighbour_tuple not in g_score or current_g_score < g_score[neighbour_tuple]:
                
                # Record where it came from
                came_from[neighbour_tuple] = (current_tuple, action)

                # Record its g_score
                g_score[neighbour_tuple] = current_g_score

                # Calculate its f_score
                f_score = current_g_score + heuristic(neighbour_board, target)

                # Add it to priority queue, with given f_score as its priority
                open_set.put(neighbour_board, f_score)

    return None  # Return None if there is no path to the goal

