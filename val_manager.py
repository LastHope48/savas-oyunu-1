import os
from basedir import BASE_DIR
import logging
from flags import Flag
import json
from typing import overload, Any, NoReturn, Literal
from copy import deepcopy

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(filename)s: %(lineno)d [%(funcName)s] | %(message)s',
    filename="game.log"
)

class NOTLOADED(Flag):
    pass

class NOVALUE(Flag):
    pass

class ValueManager:
    def __init__(self, filename: str | os.PathLike | None = None):
        self.filename = filename or os.path.join(BASE_DIR, r"values.dat")

        self.values: dict[str, Any] = {
            "kill": 1,
            "win": 0
        }

        self.defaults = deepcopy(self.values)

        self.load(create_file=True)

    def load(self, *, create_file: bool=False):
        try:
            with open(self.filename, "r", encoding="utf-8") as file:
                data = file.read()
                self.values = json.loads(data)

        except EOFError:
            logging.error("{} cannot be readed. (raised EOFError)".format(self.filename))

            if create_file:
                self.save()

            else:
                for key in self.values.keys():
                    self.values[key] = NOTLOADED
        
        except FileNotFoundError:
            logging.warning(f"{self.filename} not found and caused FileNotFoundError.")

            if create_file:
                self.save()

            else:
                for key in self.values.keys():
                    self.values[key] = NOTLOADED

    def save(self):
        print(self.values)

        with open(self.filename, "w", encoding="utf-8") as file:
            try:
                json.dump(self.values, file, indent=4, ensure_ascii=True)

            except json.JSONDecodeError as e:
                logging.error(f"json module throwed an exception: {e}")

    def set_val(self, key: str, value: Any):
        assert key in self.values.keys(), f"{key} not found."

        self.values[key] = value

    def get_val(self, key: str):
        return self.values.get(key, NOVALUE)

    @overload
    def __call__(self, key: str) -> Any: ...

    @overload
    def __call__(self, key: str, value: Any) -> NoReturn: ...

    @overload
    def __call__(self, key: str, value: Any, mode: str | Literal["set"] | Literal["change"]) -> NoReturn: ...

    def __call__(self, key: str, value: Any | NOVALUE=NOVALUE, mode="set"):

        if type(value) == NOVALUE or value == NOVALUE:
            get_value = self.values.get(key)

            if get_value is NOTLOADED:
                get_value = self.defaults.get(key)

            return get_value

        if mode == "set":
            self.values[key] = value

        elif mode == "change":
            self.values[key] += value

        else:
            raise ValueError
