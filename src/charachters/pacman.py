from src.enums import Direction
from src.vector import Pos2D

from .abstract_chars import MovingEntities
from ..config import Config
import pygame




class Pacman(MovingEntities):
	anim_frames = [pygame.image.load(f"assets/pacman/frame_{num}.png") for num in range(4)]


	def __init__(self, context: "PacMap", direction: Direction, x: int=0, y: int=0, lives:int=3):
		super().__init__(context, direction, x, y)
		self.lives = lives
		self.cheat_mode = False

	@property
	def image(self):
		frame = self.anim_frames[self.anim_step]
		rotated = self.direction.rotate(frame)
		scaled = pygame.transform.scale(rotated, (Config.cell_size*1.5, Config.cell_size* 1.5))
		return scaled

	def incr_anim(self):
		self.anim_step = (self.anim_step + 1) % len(self.anim_frames)

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
			if self.cheat_mode:
				self.direction = self.next_direction #fast turn in cheat mode
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

	def eat_wall(self):
		if self.cheat_mode:
			facing_cell_x, facing_cell_y = (self.next_pos  //3) + self.direction.delta()
			if not (0 <= facing_cell_x < len(self.map.cells) and  0<= facing_cell_y < len(self.map.cells[0])):
				return
			cell_x, cell_y = self.next_pos //3
			self.map.cells[cell_x][cell_y].walls &= ~self.direction.value
			self.map.cells[facing_cell_x][facing_cell_y].walls &= ~self.direction.oppo().value
			self.map.cells[cell_x][cell_y].init_image()
			for neig_x, neig_y in [(Pos2D(cell_x, cell_y)) + direc.delta() for direc in Direction]:
				if 0<= neig_x < len(self.map.cells) and  0<= neig_y < len(self.map.cells[0]):
					cell = self.map.cells[neig_x][neig_y]
					cell.init_image()
			