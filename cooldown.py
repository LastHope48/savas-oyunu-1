class Cooldown:
    def __init__(self, *durations):
        self.durations = durations
        self.cooldown = self.durations[0]

    def reduce(self, dt: int):
        self.cooldown -= dt


    def check(self):
        return self.cooldown <= 0

    def refresh(self, index=0):
        self.cooldown = self.durations[index]

    def __add__(self, other):
        if isinstance(other, int):
            return Cooldown(self.durations[0] + other)

        elif isinstance(other, Cooldown):
            return Cooldown(self.durations[0] + other.durations[0])

        else:
            raise TypeError
