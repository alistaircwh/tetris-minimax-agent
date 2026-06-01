# COMP30024 Artificial Intelligence, Semester 1 2024
# Project Part A: Single Player Tetress

from referee.game.coord import Vector2
from dataclasses import dataclass

# Another class similar to PlaceAction, except that it can represent vectors outside the board
# This allows for shapes to be defined as offsets of a coordinate (allows negatives)
@dataclass(frozen=True, slots=True)
class PlaceTemplate():
    """
    A dataclass representing a "place template", where four vectors
    denote the shape of a tetromino piece without specific board placement.
    """
    v1: Vector2
    v2: Vector2
    v3: Vector2
    v4: Vector2

    @property
    def vectors(self) -> set[Vector2]:
        return {self.v1, self.v2, self.v3, self.v4}

    def __str__(self) -> str:
        return f"TEMPLATE({self.v1}, {self.v2}, {self.v3}, {self.v4})"

# Each possible tetrimono shape has been defined relative to being placed above a coordinate at (0,0)
# This includes translations
tetromino_template = [
    # 'I' shapes
    PlaceTemplate(Vector2(-1, 0), Vector2(-2, 0), Vector2(-3, 0), Vector2(-4, 0)),  # Vertical
    PlaceTemplate(Vector2(-1, 0), Vector2(-1, -1), Vector2(-1, -2), Vector2(-1, -3)),  # Horizontal 1
    PlaceTemplate(Vector2(-1, 0), Vector2(-1, 1), Vector2(-1, -1), Vector2(-1, -2)),  # Horizontal 2
    PlaceTemplate(Vector2(-1, 0), Vector2(-1, 1), Vector2(-1, 2), Vector2(-1, -1)),  # Horizontal 3
    PlaceTemplate(Vector2(-1, 0), Vector2(-1, 2), Vector2(-1, 1), Vector2(-1, 3)),  # Horizontal 4

    # 'O' shape
    PlaceTemplate(Vector2(-1, 0), Vector2(-1, 1), Vector2(-2, 1), Vector2(-2, 0)),  # 1
    PlaceTemplate(Vector2(-1, 0), Vector2(-1, -1), Vector2(-2, 0), Vector2(-2, -1)),  # 2

    # 'T' shapes
    PlaceTemplate(Vector2(-1, 0), Vector2(-2, 0), Vector2(-2, -1), Vector2(-2, 1)),  # T pointing up
    PlaceTemplate(Vector2(-1, 0), Vector2(-2, 0), Vector2(-3, 0), Vector2(-2, -1)),  # T pointing left 1
    PlaceTemplate(Vector2(-1, 0), Vector2(-1, 1), Vector2(-2, 1), Vector2(0, 1)),  # T pointing left 2, shifted right and down
    PlaceTemplate(Vector2(-1, 0), Vector2(-2, 0), Vector2(-3, 0), Vector2(-2, 1)),  # T pointing right 1
    PlaceTemplate(Vector2(-1, 0), Vector2(-1, -1), Vector2(-2, -1), Vector2(0, -1)),  # T pointing right 2, shifted left and down
    PlaceTemplate(Vector2(-1, 0), Vector2(-2, 0), Vector2(-1, -1), Vector2(-1, 1)),  # T pointing down 1
    PlaceTemplate(Vector2(-1, 0), Vector2(-2, 1), Vector2(-1, 1), Vector2(-1, 2)),  # T pointing down 2, shifted right
    PlaceTemplate(Vector2(-1, 0), Vector2(-2, -1), Vector2(-1, -2), Vector2(-1, -1)),  # T pointing down 3, shifted left

    # 'L' shapes
    PlaceTemplate(Vector2(-1, 0), Vector2(-2, 0), Vector2(-3, 0), Vector2(-3, -1)),  # L pointing left 1
    PlaceTemplate(Vector2(-1, 0), Vector2(0, 1), Vector2(-1, 1), Vector2(1, 1)),  # L pointing left 2, shifted right and down
    PlaceTemplate(Vector2(-1, 0), Vector2(-2, 0), Vector2(-3, 0), Vector2(-1, 1)),  # L pointing right 1
    PlaceTemplate(Vector2(-1, 0), Vector2(-2, -1), Vector2(-3, -1), Vector2(-1, -1)),  # L pointing right 2, shifted left
    PlaceTemplate(Vector2(-1, 0), Vector2(-1, -1), Vector2(-1, 1), Vector2(-2, 1)),  # L pointing up 1
    PlaceTemplate(Vector2(-1, 0), Vector2(-1, -1), Vector2(-1, -2), Vector2(-2, 0)),  # L pointing up 2, shifted left
    PlaceTemplate(Vector2(-1, 0), Vector2(-1, 1), Vector2(-1, 2), Vector2(-2, 2)),  # L pointing up 3, shifted right
    PlaceTemplate(Vector2(-1, 0), Vector2(-2, 0), Vector2(-2, 1), Vector2(-2, 2)),  # L pointing down 1
    PlaceTemplate(Vector2(-1, 0), Vector2(0, -2), Vector2(-1, -1), Vector2(-1, -2)),  # L pointing down 2, shifted left and down

    # 'J' shapes
    PlaceTemplate(Vector2(-1, 0), Vector2(-2, 0), Vector2(-3, 0), Vector2(-1, -1)),  # J pointing left 1
    PlaceTemplate(Vector2(-1, 0), Vector2(-2, 1), Vector2(-3, 1), Vector2(-1, 1)),  # J pointing left 2, shifted right
    PlaceTemplate(Vector2(-1, 0), Vector2(-2, 0), Vector2(-3, 0), Vector2(-3, 1)),  # J pointing right 1
    PlaceTemplate(Vector2(-1, 0), Vector2(0, -1), Vector2(-1, -1), Vector2(1, -1)),  # J pointing right 2, shifted left and down
    PlaceTemplate(Vector2(-1, 0), Vector2(-1, 1), Vector2(-1, -1), Vector2(-2, -1)),  # J pointing up 1
    PlaceTemplate(Vector2(-1, 0), Vector2(-1, -1), Vector2(-1, -2), Vector2(-2, -2)),  # J pointing up 2, shifted left
    PlaceTemplate(Vector2(-1, 0), Vector2(-1, 1), Vector2(-1, 2), Vector2(-2, 0)),  # J pointing up 3, shifted right
    PlaceTemplate(Vector2(-1, 0), Vector2(-2, 0), Vector2(-2, -1), Vector2(-2, -2)),  # J pointing down 1
    PlaceTemplate(Vector2(-1, 0), Vector2(-1, 2), Vector2(-1, 1), Vector2(0, 2)),  # J pointing down 2, shifted right and down

    # 'S' shapes
    PlaceTemplate(Vector2(-1, 0), Vector2(-1, -1), Vector2(-2, 0), Vector2(-2, 1)),  # S pointing up/down 1
    PlaceTemplate(Vector2(-1, 0), Vector2(-1, 1), Vector2(-2, 1), Vector2(-2, 2)),  # S pointing up/down 2, shifted right
    PlaceTemplate(Vector2(-1, 0), Vector2(-2, 0), Vector2(-2, -1), Vector2(-3, -1)),  # S pointing left/right 1
    PlaceTemplate(Vector2(-1, 0), Vector2(-1, 1), Vector2(0, 1), Vector2(-2, 0)),  # S pointing left/right 2, shifted right and down

    # 'Z' shapes
    PlaceTemplate(Vector2(-1, 0), Vector2(-1, 1), Vector2(-2, 0), Vector2(-2, -1)),  # Z pointing up/down 1
    PlaceTemplate(Vector2(-1, 0), Vector2(-1, -1), Vector2(-2, -1), Vector2(-2, -2)),  # Z pointing up/down 2, shifted left
    PlaceTemplate(Vector2(-1, 0), Vector2(-2, 0), Vector2(-2, 1), Vector2(-3, 1)),  # Z pointing left/right 1
    PlaceTemplate(Vector2(-1, 0), Vector2(-1, -1), Vector2(0, -1), Vector2(-2, 0)),  # Z pointing left/right 2, shifted left and down
]

# Function called to create similar templates, but rotated so that shapes are placed on the right/left/bottom of the (0,0) coordinate
def rotate_tetrominos_90_degrees(tetromino_template):
    rotated_template = []

    # Loops through the shapes
    for tetromino in tetromino_template:
        rotated_vectors = []

        # Loops through the vectors of the shape
        for vector in tetromino.vectors:

            # Converts the vector to what it would be if rotated 90 degrees
            r, c = vector.r, vector.c
            rotated_vector = Vector2(c, -r)
            rotated_vectors.append(rotated_vector)
        
        # Collates the vectors the have the entire shape rotated 90 degrees
        rotated_tetromino = PlaceTemplate(*rotated_vectors)
        rotated_template.append(rotated_tetromino)

    # Returns the entire template rotated 90 degrees
    return rotated_template

# Create the rotated versions of the tetromino templates in every direction
tetromino_template_90 = rotate_tetrominos_90_degrees(tetromino_template)
tetromino_template_180 = rotate_tetrominos_90_degrees(tetromino_template_90)
tetromino_template_270 = rotate_tetrominos_90_degrees(tetromino_template_180)

 # Put into a list to iterate over
all_templates = [tetromino_template, tetromino_template_90, tetromino_template_180, tetromino_template_270]