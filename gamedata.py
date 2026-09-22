import classes
from copy import deepcopy

class GameData:
    def __init__(
            self,
            player: classes.Player = None,
            world: classes.World = None
    ):

        self.player = player
        self.world = world

        self.level = 1
        self.enemy_data: dict[int, classes.Enemy] = {}

        self.win = False

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