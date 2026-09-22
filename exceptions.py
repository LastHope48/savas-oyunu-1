class GameError(Exception):
    pass


class HealthError(GameError):
    def __init__(self, expected_id, expected_ver, given_id, given_ver, path, checks: tuple):

        self.expected_id = expected_id
        self.expected_ver = expected_ver
        self.given_id = given_id
        self.given_ver = given_ver
        self.path = path
        self.checks = checks

        message = (
            f"{path} yolundaki ayarlar dosyasının sağlık kontrolü negatif çıktı.\n"
            f"{given_id} ve {given_ver} bilgileri olması gereken {expected_id} ve {expected_ver} bilgileriyle uyuşmuyor. "
            "Kontroller: {} | {} | {}".format(*(f"check{i+1}: {check}" for i, check in enumerate(checks)))
        )

        super().__init__(message)


class EnemyPositionError(GameError):
    def __init__(self, name, deneme, level):

        self.name = name
        self.deneme = deneme
        self.level = level

        message = (
            f"{level} içindeki {name} adlı düşmanın (Enemy) pozisyonu ayarlanamadı. "
            f"{deneme} deneme yapıldı."
        )

        super().__init__(message)


class InvalidGameStateError(GameError):
    def __init__(self, state):
        super().__init__(f"Oyun durumu {state} geçerli değil.")
