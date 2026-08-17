from hmac import new

import pygame

from .enums import Direction
from abc import ABC, abstractmethod
from typing import Optional
from .vector import Pos2D

class MovingEntities(ABC):
	def __init__(self, context: 'PacMap', direction: Direction, x: int=0, y: int=0):
		self.pos = Pos2D(x * 3, y *3) + (1, 1)
		self.offset = 0
		self.direction = direction 
		self.next_direction = direction
		self.is_alive = True
		self.map = context
		self.next_pos = self.pos

	@abstractmethod
	def update(self, dt:float):
		pass

	def move(self, new_pos: Pos2D):
		self.pos = self.next_pos
		self.next_pos = new_pos

	@property
	def visual_pos(self):
		return (self.pos - (0.25,0.25)).lerp(self.next_pos - (0.25, 0.25), self.offset)

	@property
	def cell_pos(self):
		return (self.pos) // 3


class Pacman(MovingEntities):
	anim_step = 0
	anim_frames = [pygame.image.load(f"assets/pacman/frame_{num}.png") for num in range(4)]

	def update(self, dt:float):
		self.offset += dt

		if self.offset >= 1:
			self.offset -= 1
			self.step()

	def step(self):
		self.move(self.turn_and_pathfind())
		cell_x, cell_y = self.cell_pos
		if self.map.cells[cell_x][cell_y].fruit is not None:
			self.map.score += self.map.cells[cell_x][cell_y].fruit.eated()

	def turn_and_pathfind(self):
		new_pos = self.next_pos
		cell_x, cell_y = (new_pos) // 3
		cell_walls =   self.map.cells[cell_x][cell_y].walls
		if (self.next_direction != self.direction and (new_pos % (3,3)) == (1, 1)):
			if cell_walls & self.next_direction.value: #if wall blocked
				if self.next_direction != self.direction.oppo(): # fast turn back
					self.next_direction = self.direction
			else:
				self.direction = self.next_direction #empty buffer
		if (not cell_walls & self.direction.value #wall open
				or (((new_pos) % (3, 3))[0] != 1 and self.direction.delta()[0]) #or continue x
				or (((new_pos) % (3, 3))[1] != 1 and self.direction.delta()[1]) #or continue y 
			):
			new_pos += self.direction.delta()
		if (
			self.next_direction != self.direction
			and not cell_walls & self.next_direction.value
			and new_pos % (3,3) == (1, 1)
		):
			self.direction = self.next_direction
			new_pos += self.direction.delta()
		return new_pos

