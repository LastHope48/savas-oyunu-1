class Flag:
    @classmethod
    def __str__(cls):
        return cls.__doc__ or cls.__name__

class DefaultWorld(Flag):
    """__default_world__"""

class FreeplayWorld(Flag):
    """__freeplay__"""

class NoSword(Flag):
    pass

class NoItem(Flag):
    pass

class NotDataStorer(Flag):
    pass

SUCCESS = 1
FAILURE = 2