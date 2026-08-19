from enum import Enum
import pygame




class GhostState(Enum):
    CHASE = 0b1
    SCATER = 0b10
    FRIGHTENED = 0b100
    DEAD = 0b1000
    


class Direction(Enum):
    NORTH = 0b1
    EAST = 0b10
    SOUTH = 0b100
    WEST = 0b1000

    def oppo(self) -> "Direction":
        """get the opposite direction"""
        return {
            Direction.NORTH: Direction.SOUTH,
            Direction.SOUTH: Direction.NORTH,
            Direction.EAST:  Direction.WEST,
            Direction.WEST:  Direction.EAST,
        }[self]

    def delta(self) -> tuple:
        """get the delta for direction changing"""
        return {
            Direction.NORTH: (0, -1),
            Direction.SOUTH: (0, 1),
            Direction.EAST:  (1, 0),
            Direction.WEST:  (-1, 0),
        }[self]
    
    def rotate(self, sprite:pygame.Surface):
        angles = {
            Direction.NORTH: -90.0,
            Direction.EAST:  180.0,
            Direction.SOUTH: 90.0,
            Direction.WEST:  0.0,
        }
        return pygame.transform.rotate(sprite, angles[self])
        
    def pac_order(self):
        order ={
            Direction.NORTH: 1,
            Direction.EAST:  4,
            Direction.SOUTH: 3,
            Direction.WEST:  2,
        }
        return order[self]
    
    def to_text(self) -> str:
        """get the char representation of directions"""
        return {
            Direction.NORTH: 'n',
            Direction.SOUTH: 's',
            Direction.EAST:  'e',
            Direction.WEST:  'w',
        }[self]