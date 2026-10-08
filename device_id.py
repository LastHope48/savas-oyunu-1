import json
import os
import secrets
import requests
from basedir import BASE_DIR


class DeviceID:
    FILE = os.path.join(BASE_DIR, "device_id.dat")

    def __init__(self):
        if os.path.exists(self.FILE):
            self.device_id = self.load()
        else:
            self.device_id = self.create()

    def load(self):
        if not os.path.exists(self.FILE):
            raise FileNotFoundError("device_id.dat bulunamadı.")

        with open(self.FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        device_id = data["device_id"]
        hmac_value = data["hmac"]

        try:
            response = requests.post(
                "https://api.infinitesoft-tr.com/device/verify",
                json={
                    "device_id": device_id,
                    "hmac": hmac_value
                },
                timeout=10,
                verify=False
            )

            response.raise_for_status()

        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout
        ):
            raise ConnectionError("İnternet bağlantısı yok.")

        if not response.json()["valid"]:
            raise ValueError("device_id.dat geçersiz.")

        return device_id

    @staticmethod
    def create():
        device_id = secrets.token_hex(32)

        try:
            response = requests.post(
                "https://api.infinitesoft-tr.com/device/sign",
                json={
                    "device_id": device_id
                },
                timeout=10,
                verify=False
            )

            response.raise_for_status()

        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout
        ):
            raise ConnectionError("İnternet bağlantısı yok.")

        hmac_value = response.json()["hmac"]

        data = {
            "device_id": device_id,
            "hmac": hmac_value
        }

        with open(DeviceID.FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        return device_id