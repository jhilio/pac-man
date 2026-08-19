

from os import RTLD_DEEPBIND

from .moving_entity import MovingEntities,Direction, MainData, Pos2D, abstractmethod
from ..enums import GhostState



def get_ghost_state(level:dict, time_elapsed:float):
    return GhostState.CHASE




class Ghost(MovingEntities):

    def __init__(self, direction: Direction, x = 0, y = 0):
        super().__init__(direction, x, y)
        self.mode = GhostState.SCATER
        self.choose_target_cell()
        self.speed = MainData.pacmap.level["ghost_speed"] / 100
        self.fright_speed = MainData.pacmap.level["ghost_fright_speed"] / 100

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if "ghost_name" not in cls.__dict__:
            raise TypeError(
                f"{cls.__name__} must define 'ghost_name'"
            )
        if "ghost_color" not in cls.__dict__:
            raise TypeError(
                f"{cls.__name__} must define 'ghost_color'"
            )

    def rank_neighbor(self):
        new_pos = self.next_pos
        cell_x, cell_y = new_pos // 3
        if (new_pos % (3, 3) != (1,1)):
            valide_dirs = [self.direction]
        else:
            valide_dirs = [
            direc for direc in Direction 
                if (
                    not MainData.pacmap.cells[cell_x][cell_y].walls & direc.value
                    and self.direction != direc.oppo()
                )
            ]
        if not valide_dirs:
            valide_dirs = [self.direction.oppo()]
        ranked = sorted(
            valide_dirs,
            key=lambda direc: (
                (new_pos + direc.delta()).pythagore(self.target_cell),
                direc.pac_order()
            )
        )
        return ranked

    @property
    def image(self):
        if (MainData.pacmap.fright_time_left > 20
            or MainData.pacmap.fright_time_left % 4 > 1):
            frame = MainData.assets.get_asset(
                f"eyes_{self.direction.to_text()}.png",
                size_multiplier=1.3)
        else:
            frame = MainData.assets.get_asset(
                f"{self.ghost_name}_{self.direction.to_text()}{self.anim_step+1}.png",
                size_multiplier=1.3)
        return frame

    def update(self, dt:float):
        pacmap = MainData.pacmap
        if pacmap.fright_time_left:
            if self.mode != GhostState.FRIGHTENED: 
                self.mode = GhostState.FRIGHTENED
                self.direction = self.direction.oppo()
        else:
            self.mode = get_ghost_state(pacmap.level, pacmap.total_elapsed_time)
        super().update(dt)
    

    def incr_anim(self):
        self.anim_step = 0 if self.anim_step else 1

    def choose_target_cell(self):
        match self.mode:
            case GhostState.SCATER:
                self.target_cell = self.original_pos
            case GhostState.FRIGHTENED:
                self.target_cell = self.original_pos
            case GhostState.CHASE:
                self.target_cell = self.specific_chase_cell()
        if self.target_cell == self.pos:
            self.target_cell = self.original_pos

    def step(self):
        self.choose_target_cell()
        self.direction = self.rank_neighbor()[0]
        self.move(self.next_pos + self.direction.delta())

    @abstractmethod
    def specific_chase_cell(self) -> Pos2D:
        pass