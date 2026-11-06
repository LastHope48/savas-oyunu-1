import classes
from copy import deepcopy
import pygame
from classes import defaults

pygame.init()
info = pygame.display.Info()

class GameData:
    def __init__(
            self,
            player: classes.Player = None,
            world: classes.World = None
    ):

        self.player: classes.Player = player
        self.world: classes.World = world

        self.level = 1
        self.enemy_data: dict[int, classes.Enemy] = {}

        self.win = False

    def init_prepare(self):
        self.player.set_pos(self.world)
        self.world.create_rocks(info.current_w, info.current_h)

        for enemy in self.enemy_data.values():
            enemy.set_pos(self.world, info)

    @staticmethod
    def to_gamedata(obj: dict):
        obj = deepcopy(obj)

        gamedata = GameData(
            obj["Player"],
            obj["World"]
        )

        gamedata.level = int(obj["Level"].lstrip("level"))
        gamedata.enemy_data = obj["EnemyData"]

        gamedata.win = obj["Win"]

        return gamedata
