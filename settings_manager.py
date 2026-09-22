import os
import logging
from exceptions import HealthError
import copy
from flags import FAILURE

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(filename)s: %(lineno)d [%(funcName)s] | %(message)s',
    filename="game.log",
    level=logging.INFO
)


class SettingsManager:
    def __init__(self, filename: str, path: os.PathLike, game_id, game_ver):
        self.filename = filename
        self.path = path
        self.attrs = {
            "DEBUG": 1,
            "DEL_OUTPUTS": 2,
            "SAVE_LAST": 3,
            "MUSIC": 4,
            "MUSIC_PATH": 5,
            "MUSIC_LOOP": 6
        }
        self.defaults = {
            "DEBUG": False,
            "DEL_OUTPUTS": True,
            "SAVE_LAST": True,
            "MUSIC": False,
            "MUSIC_PATH": "...",
            "MUSIC_LOOP": -1
        }
        self.types = {
            "DEBUG": bool,
            "DEL_OUTPUTS": bool,
            "SAVE_LAST": bool,
            "MUSIC": bool,
            "MUSIC_PATH": str,
            "MUSIC_LOOP": int
        }
        self.linenum = 7
        self.game_id = game_id
        self.game_ver = game_ver
        self.created = False

    def read(self):
        if not self.created:
            logging.warning("Settings file not created.")
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            try:
                logging.info(f"Reading settings file {self.path}")
                with open(self.path, "r", encoding="utf-8") as f:
                    return f.read()
            except FileNotFoundError:
                logging.critical(f"Settings file not found in path '{self.path}'")
                print(f"Dosya Bulunamadı: {self.path}")
                return None
            except PermissionError:
                logging.error("Settings file cannot be reached due to permission error.")
                print("İzin verilmedi.")
                return None

    def repair_health(self):
        if not self.created:
            logging.warning("Settings file not created.")
            return
        data = self.read()
        lines = data.splitlines()
        lines[0] = self.return_health_text()
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        logging.info("Setting file repaired.")

    def return_health_text(self):
        return f"[{self.game_id}|{self.game_ver}]BATTLEGAME"

    def create(self, check=True, add_defaults=True):
        if not check or not os.path.exists(self.path):

            lines = [self.return_health_text()]
            if add_defaults:
                for key in self.defaults:
                    lines.append(str(self.defaults[key]))
            with open(self.path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            self.created = True
            logging.info(f"Created settings file in '{self.path}'")
        else:
            self.created = True

    def check_health(self, *, log=True):
        if not self.created:
            logging.warning("Settings file not created.")
            return
        data = self.read()
        if not data:
            return False
        lines_number = len(data.splitlines())
        lines = data.splitlines()
        first_line = data.split("\n")[0]
        parts = first_line.split("|")
        self._parts = copy.deepcopy(parts)
        check1 = (
            parts[0] == f"[{self.game_id}"
            and parts[1] == f"{self.game_ver}]BATTLEGAME"
            and first_line.endswith("BATTLEGAME")
        )
        check2 = lines_number == self.linenum
        if not check2:
            self.checks = (check1, False, "Ulaşılamadı.")
            return False
        check3 = True
        
        for i, v_type in enumerate(self.types.values(), start=1):

            value = lines[i]

            if value.lower() in ["false", "true"]:
                check3 = check3 and v_type == bool

            elif value.lstrip("-").isnumeric():
                check3 = check3 and v_type == int

            else:
                check3 = check3 and v_type == str
        self.checks = (check1, check2, check3)
        result = (check1 and check2 and check3)
        if log: logging.info(f"Health check result: {result}")
        return result

    def get_attribute(self, name, *, log=True):
        if not self.created:
            if log: logging.warning("Settings file not created.")
            return
        if not self.check_health(log=log):
            raise HealthError(self.game_id, self.game_ver, self._parts[0], self._parts[1], self.path, self.checks)

        line = self.attrs[name]
        value = self.read().splitlines()[line]
        value_type = self.types[name]
        if log: logging.info(f"Got attribute {name} with value '{value}'")
        if value_type == bool:
            return value.lower() == "true"
        elif value_type == str:
            return value
        elif value_type == int:
            return int(value)

    def write_attribute(self, name, value):
        if not self.created:
            logging.warning("Settings file not created.")
            return FAILURE, "Settings file not created."
        assert self.check_health()
        if value.lower() in ["true", "false"]:
            value = value.lower() == "true"
        try:
            line = self.attrs[name]
        except KeyError:
            logging.error(f"{name} is not in settings attributes.")
            return FAILURE, f"{name} is not in settings attributes."

        expected_type = self.types[name]

        if expected_type == int and isinstance(value, str):
            if value.lstrip("-").isnumeric():
                value = int(value)
            else:
                logging.warning(f"Given value {value} is not an {expected_type}")
                return FAILURE, f"Given value {value} is not an {expected_type}"

        elif type(value) is not expected_type:
            logging.warning(f"Given value {value} is not a {expected_type}")
            return FAILURE, f"Given value {value} is not a {expected_type}"
        data = self.read().splitlines()
        data[line] = str(value)

        with open(self.path, "w", encoding="utf-8") as f:
            f.write("\n".join(data))
        logging.info(f"Written attribute '{name}' with value '{value}'.")
