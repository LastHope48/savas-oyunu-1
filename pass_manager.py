import logging
import os

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(filename)s: %(lineno)d [%(funcName)s] | %(message)s',
    filename="game.log"
)

try:
    import hashlib
except ImportError as e:
    logging.critical(f"Importing hashlib failed with ImportError. Error message: {e}")
except Exception as e:
    logging.critical(f"Importing hashlib failed. Error message: {e}")


class HashManager:
    def __init__(self, filename="securedvars"):
        self.filename = filename

    def hash(self, text: str):
        hashed = hashlib.sha256(text.encode()).digest()
        logging.info("Hashing started.")
        for _ in range(100):
            hashed = hashlib.sha256(hashed).digest()

        logging.info(f"Hashed {text} successfully.")
        return hashed.hex()

    def write(self, text: str):
        hashed = self.hash(text)

        with open(self.filename, "r", encoding="utf-8") as f:
            file = f.read()
        logging.info(f"File {self.filename} readed successfully.")
        data = file + "\n" + hashed
        logging.info("Assemblying file and hashed text.")
        with open(self.filename, "w", encoding="utf-8") as f:
            f.write(data)
        logging.info(f"Writing file {self.filename}.")

    def check(self, text: str, line: int):
        hashed_control = self.hash(text)

        with open(self.filename, "r", encoding="utf-8") as f:
            file = f.read()

        splitted = file.splitlines()

        if hashed_control == splitted[line]:
            return True

        return False

    def fcheck(self, filename=None):
        checking_filename = filename or self.filename

        root_dir = os.listdir()

        if checking_filename in root_dir:
            return True

        return False
