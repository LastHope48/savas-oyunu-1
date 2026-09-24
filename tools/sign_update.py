import hashlib
from pathlib import Path

from cryptography.hazmat.primitives import serialization


PROJECT_DIR = Path(__file__).resolve().parent.parent

ZIP_FILE = PROJECT_DIR / "savas_oyunu1-linux.zip"

PRIVATE_KEY_FILE = (
    Path.home()
    / "secret_keys"
    / "private_key.pem"
)

SIGNATURE_FILE = (
    PROJECT_DIR
    / "savas_oyunu1-linux.zip.sig"
)


def calculate_sha256(path):
    sha256 = hashlib.sha256()

    with open(path, "rb") as file:
        while chunk := file.read(1024 * 1024):
            sha256.update(chunk)

    return sha256.digest()


with open(PRIVATE_KEY_FILE, "rb") as file:
    private_key = serialization.load_pem_private_key(
        file.read(),
        password=None
    )


file_hash = calculate_sha256(ZIP_FILE)

signature = private_key.sign(file_hash)

SIGNATURE_FILE.write_bytes(signature)

print("İmzalama başarılı!")
print("İmza:", SIGNATURE_FILE)