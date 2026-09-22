import pickle
import _pickle
import os
from datetime import datetime
import logging

logging.basicConfig(
    filename="game.log",
    format='%(asctime)s - %(levelname)s - %(filename)s: %(lineno)d [%(funcName)s] | %(message)s',
    level=logging.INFO
)


class SaveManager:
    def __init__(self, path="saves"):
        self.path = path
        os.makedirs(path, exist_ok=True)
        logging.info("Save manager initialized.")

    def save(self, slot: int, data, version):
        print("save başladı")
        save_data = {
            "info": {
                "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
                "id": slot
            },
            "data": data,
            "version": version
        }

        filename = os.path.join(self.path, f"save{slot}.save")
        print("Kaydedilecek: ", save_data.keys() )
        with open(filename, "wb") as file:
            pickle.dump(save_data, file)
        print("kaydedildi")
        print(filename)
        logging.info(f"Saved game slot{slot}")

    def load(self, slot: int):
        filename = os.path.join(self.path, f"save{slot}.save")

        if not os.path.exists(filename):
            print("Bulunamadı")
            return None

        with open(filename, "rb") as file:
            save = pickle.load(file)["data"]

        logging.info(f"Loaded slot {slot}")
        return save

    def get_info(self, slot: int) -> dict | None:
        filename = os.path.join(self.path, f"save{slot}.save")

        if not os.path.exists(filename):
            return None

        with open(filename, "rb") as file:
            logging.info(f"Returning info slot{slot}")
            data = pickle.load(file)["info"]
            logging.info(f"DATA: {data}")
            return data

    def delete(self, slot: int):
        filename = os.path.join(self.path, f"save{slot}.save")

        if os.path.exists(filename):
            os.remove(filename)
        logging.info(f"Deleted save with slot{slot}")

    def save_last_slot(self, data):

        save_data = {
            "info": {
                "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
                "version": 1,
                "corrupted": False
            },
            "data": data
        }
        with open(os.path.join(self.path, "last.save"), "wb") as file:
            pickle.dump(save_data, file)
        logging.info("Saved last slot.")

    def get_version(self, slot: int) -> str:
        filename = os.path.join(self.path, f"save{slot}.save")

        with open(filename, "rb") as file:
            ver = pickle.load(file)["version"]
            logging.info(f"Slot version returning: '{ver}'")
            return ver

    def last_slot(self, log=True):
        filename = os.path.join(self.path, "last.save")

        if not os.path.exists(filename):
            return None

        with open(filename, "rb") as file:
            try:
                if log:
                    logging.info("Trying to return last slot data...")
                return pickle.load(file)["data"]
            except _pickle.UnpicklingError:
                if log:
                    logging.warning("Last slot corrupted.")
                return None

            except EOFError:
                if log:
                    logging.warning("Last slot is empty.")
                return None

    def get_info_last_slot(self, *, log=True):
        filename = os.path.join(self.path, "last.save")

        if not os.path.exists(filename):
            return None

        with open(filename, "rb") as file:
            try:
                if log:
                    logging.info("Trying to return last slot info...")
                return pickle.load(file)["info"]
            except _pickle.UnpicklingError:
                if log:
                    logging.warning("Last slot corrupted.")
                return {
                "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
                "version": 1,
                "corrupted": True
                }
            except Exception as e:
                if log:
                    logging.error(f"Getting last slot info raised error: {e}")
                return {
                "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
                "version": -1,
                "unknown": True,
                "error": e
                }

    def delete_last_slot(self):
        filename = os.path.join(self.path, "last.save")

        if not os.path.exists(filename):
            return None

        os.remove(filename)

    def list_saves(self):
        listed = os.listdir(self.path)
        listed.remove("last.save")
        return listed

    def reset(self):
        for file in os.listdir(self.path):
            os.remove(os.path.join(self.path, file))

    def get_all_infos(self):
        infos = {}

        for filename in os.listdir(self.path):
            if filename == "last.save":
                continue

            path = os.path.join(self.path, filename)

            with open(path, "rb") as f:
                try:
                    save = pickle.load(f)
                except _pickle.UnpicklingError:
                    logging.warning(f"Save '{filename}' is corrupted.")
                    continue
                except EOFError:
                    logging.warning(f"Loading save '{filename}' caused EOFError")
                    continue

            info = save["info"]
            info["version"] = save["version"]

            infos[info["id"]] = info

        return infos
