# COMP30024 Artificial Intelligence, Semester 1 2024
# Project Part A: Single Player Tetress

from enum import Enum
from dataclasses import dataclass
from typing import Generator

import heapq
import itertools


# WARNING: Please *do not* modify any of the code in this file, as this could
#          break things in the submission environment. Failed test cases due to
#          modification of this file will not receive any marks. 
#
#          To implement your solution you should modify the `search` function
#          in `program.py` instead, as discussed in the specification.

BOARD_N = 11


class PlayerColor(Enum):
    """
    An `enum` capturing the two player colours.
    """
    RED = 0
    BLUE = 1

    def __str__(self) -> str:
        """
        String representation of a player colour identifier.
        """
        return {
            PlayerColor.RED: "RED",
            PlayerColor.BLUE: "BLUE"
        }[self]


@dataclass(frozen=True, slots=True)
class Vector2:
    """
    A simple 2D vector "helper" class with basic arithmetic operations
    overloaded for convenience.
    """
    r: int
    c: int

    def __lt__(self, other: 'Vector2') -> bool:
        return (self.r, self.c) < (other.r, other.c)
    
    def __hash__(self) -> int:
        return hash((self.r, self.c))
    
    def __str__(self) -> str:
        return f"Vector2({self.r}, {self.c})"

    def __add__(self, other: 'Vector2|Direction') -> 'Vector2':
        return self.__class__(self.r + other.r, self.c + other.c)

    def __sub__(self, other: 'Vector2|Direction') -> 'Vector2':
        return self.__class__(self.r - other.r, self.c - other.c)

    def __neg__(self) -> 'Vector2':
        return self.__class__(self.r * -1, self.c * -1)

    def __mul__(self, n: int) -> 'Vector2':
        return self.__class__(self.r * n, self.c * n)

    def __iter__(self) -> Generator[int, None, None]:
        yield self.r
        yield self.c

    def down(self, n: int = 1) -> 'Vector2':
        return self + Direction.Down * n
    
    def up(self, n: int = 1) -> 'Vector2':
        return self + Direction.Up * n
    
    def left(self, n: int = 1) -> 'Vector2':
        return self + Direction.Left * n
    
    def right(self, n: int = 1) -> 'Vector2':
        return self + Direction.Right * n


class Direction(Enum):
    """
    An `enum` capturing the four cardinal directions on the game board.
    """
    Down  = Vector2(1, 0)
    Up    = Vector2(-1, 0)
    Left  = Vector2(0, -1)
    Right = Vector2(0, 1)

    @classmethod
    def _missing_(cls, value: tuple[int, int]):
        for item in cls:
            if item.value == Vector2(*value):
                return item
        raise ValueError(f"Invalid direction: {value}")

    def __neg__(self) -> 'Direction':
        return Direction(-self.value)

    def __mul__(self, n: int) -> 'Vector2':
        return self.value * n

    def __str__(self) -> str:
        return {
            Direction.Down:  "[↓]",
            Direction.Up:    "[↑]",
            Direction.Left:  "[←]",
            Direction.Right: "[→]",
        }[self]

    def __getattribute__(self, __name: str) -> int:
        match __name:
            case "r":
                return self.value.r
            case "c":
                return self.value.c
            case _:
                return super().__getattribute__(__name)


@dataclass(order=True, frozen=True)
class Coord(Vector2):
    """
    A specialisation of the `Vector2` class, representing a coordinate on the
    game board. This class also enforces that the coordinates are within the
    bounds of the game board, or in the case of addition/subtraction, using
    modulo arithmetic to "wrap" the coordinates at the edges of the board.
    """

    def __post_init__(self):
        if not (0 <= self.r < BOARD_N) or not (0 <= self.c < BOARD_N):
            raise ValueError(f"Out-of-bounds coordinate: {self}")

    def __str__(self):
        return f"{self.r}-{self.c}"

    def __add__(self, other: 'Direction|Vector2') -> 'Coord':
        return self.__class__(
            (self.r + other.r) % BOARD_N, 
            (self.c + other.c) % BOARD_N,
        )

    def __sub__(self, other: 'Direction|Vector2') -> 'Coord':
        return self.__class__(
            (self.r - other.r) % BOARD_N, 
            (self.c - other.c) % BOARD_N
        )

@dataclass(frozen=True, slots=True)
class PlaceAction():
    """
    A dataclass representing a "place action", where four board coordinates
    denote the placement of a tetromino piece.
    """
    c1: Coord
    c2: Coord
    c3: Coord
    c4: Coord

    @property
    def coords(self) -> set[Coord]:
        try:
            return set([self.c1, self.c2, self.c3, self.c4])
        except:
            raise AttributeError("Invalid coords")

    def __str__(self) -> str:
        try:
            return f"PLACE({self.c1}, {self.c2}, {self.c3}, {self.c4})"
        except:
            return f"PLACE(<invalid coords>)"

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
    
# Another class, extension from the heapq. Data structure to help keep track of which nodes to explore first.
class PriorityQueue:
    def __init__(self):
        self.elements = []
        # Implement counter for tie-breaking
        self.counter = itertools.count()  
    
    def empty(self):
        return len(self.elements) == 0
    
    def put(self, item, priority):
        heapq.heappush(self.elements, (priority, next(self.counter), item))
    
    def get(self):
         # Return only the item
        return heapq.heappop(self.elements)[2] 