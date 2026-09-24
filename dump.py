from typing import overload

class Dump:
    def __init__(self):
        self.values = {}

    def get(self, name: str):
        return self.values[name]

    @overload
    def __call__(self, name: str) -> object:
        ...

    @overload
    def __call__(self, name: str, value: object) -> None:
        ...

    def __call__(self, name: str, *args):
        if len(args) == 0:
            return self.values[name]

        if len(args) == 1:
            self.values[name] = args[0]
            return

        raise TypeError(
            f"__call__() takes 1 or 2 arguments, but {len(args) + 1} were given"
        )


    def __getattribute__(self, name):
        values = object.__getattribute__(self, "values")

        if name in values:
            return values[name]

        return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        if name == "values":
            object.__setattr__(self, name, value)
        else:
            self.values[name] = value
