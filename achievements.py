import json
import os
from basedir import BASE_DIR
import requests
from device_id import DeviceID
from lang_support import Lang
import pygame


DEBUG = False
DOMAIN = r"api.infinitesoft-tr.com"

class Achievements:
    FILE = os.path.join(BASE_DIR, "achievements.dat")

    def __init__(self, device: DeviceID):
        self.device = device
        self.illegal = False

        self.achievements = {
            "win": {
                "unlocked": False,
                "hmac": None
            }
        }

        self.achievements_metadata: dict[str, dict[str, Lang | str]] = {
            "win": {
                "title": Lang(türkçe="Kazandın", english="You Won!"),
                "description": Lang(türkçe="Tebrikler, zorlu mücadelelerden sonra oyunu kazandın!", english="Congrulations, after having difficult challanges you won the game!"),
                "image": pygame.image.load(os.path.join(BASE_DIR, r"images/crown.png"))
            }
        }

        try:
            self.load()
        except (ValueError, FileNotFoundError):
            self.illegal = True

    def load(self):
        if not os.path.exists(self.FILE):
            self.save()
            return

        with open(self.FILE, "r", encoding="utf-8") as f:
            self.achievements = json.load(f)

    def save(self):
        with open(self.FILE, "w", encoding="utf-8") as f:
            json.dump(
                self.achievements,
                f,
                indent=4
            )

    def unlock(self, achievement_id):
        url = (
            "http://api.localhost:5000/achievements/unlock"
            if DEBUG
            else f"https://{DOMAIN}/achievements/unlock"
        )

        print("UNLOCK URL:", url)

        try:
            response = requests.post(
                url,
                json={
                    "achievement_id": achievement_id,
                    "device_id": self.device.device_id
                },
                timeout=10
            )

        except (
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectionError
        ) as e:
            print("API'ye ulaşılamadı:", repr(e))
            return False

        except Exception as e:
            print("UNLOCK BEKLENMEYEN HATA:", repr(e))
            raise

        print("UNLOCK STATUS:", response.status_code)
        print("UNLOCK RESPONSE:", response.text)

        if response.status_code != 200:
            return False

        data = response.json()

        self.achievements[achievement_id]["unlocked"] = True
        self.achievements[achievement_id]["hmac"] = data["hmac"]

        self.save()

        print("ACHIEVEMENT UNLOCKED:", achievement_id)

        return True

    def verify(self, achievement_id):
        achievement = self.achievements.get(achievement_id)

        if achievement is None:
            return False

        if not achievement["unlocked"]:
            return False

        try:
            response = requests.post(
                f"https://{DOMAIN}/achievements/verify",
                json={
                    "achievement_id": achievement_id,
                    "device_id": self.device.device_id,
                    "hmac": achievement["hmac"]
                },
                timeout=10,
                verify=False
            )

        except (
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectionError
        ) as e:
            print("API bağlantı hatası:", repr(e))
            return None

        except Exception as e:
            print("API'de beklenmeyen hata:", repr(e))
            raise

        if response.status_code != 200:
            print(
                "API HTTP hatası:",
                response.status_code,
                response.text
            )
            return False

        return response.json()["valid"]

    def is_online(self):
        try:
            response = requests.get(
                "http://api.localhost:5000/health" if DEBUG else f"https://{DOMAIN}/health",
                timeout=10,
                verify=False
            )

            return response.status_code == 200

        except (
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectionError
        ) as e:
            print("API'ye ulaşılamadı:", repr(e))
            return False

        except Exception as e:
            print("ACHIEVEMENT VERIFY BEKLENMEYEN HATA:", repr(e))
            raise
