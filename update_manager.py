import os
import platform
import shutil
import zipfile
import hashlib
from pathlib import Path
import sys

from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

import requests
from packaging.version import Version

from version import VERSION


if getattr(sys, "frozen", False):
    # PyInstaller
    GAME_DIR = Path(sys.executable).parent
else:
    # Normal Python
    GAME_DIR = Path(__file__).resolve().parent

GITHUB_API = (
    "https://api.github.com/repos/"
    "LastHope48/savas-oyunu-1/releases/latest"
)


UPDATE_DIR = GAME_DIR / "_update"


UPDATE_ZIP = UPDATE_DIR / "update.zip"
UPDATE_FILES_DIR = UPDATE_DIR / "files"
SIGNATURE_FILE = UPDATE_DIR / "update.zip.sig"
PUBLIC_KEY_FILE = GAME_DIR / "public_key.pem"


def get_latest_release():

    response = requests.get(
        GITHUB_API,
        verify=False,
        timeout=10,
        headers={
            "Accept": "application/vnd.github+json"
        }
    )

    response.raise_for_status()

    return response.json()


def check_for_update():

    release = get_latest_release()

    latest_version = release["tag_name"].lstrip("v")

    current_version = Version(VERSION)
    remote_version = Version(latest_version)

    if remote_version <= current_version:
        return None

    if platform.system() == "Linux":

        asset_name = "savas_oyunu1-linux.zip"

    elif platform.system() == "Windows":

        asset_name = "savas_oyunu1-windows.zip"

    else:

        raise RuntimeError(
            f"Desteklenmeyen işletim sistemi: "
            f"{platform.system()}"
        )

    update_asset = None
    signature_asset = None

    for asset in release["assets"]:

        if asset["name"] == asset_name:
            update_asset = asset

        elif asset["name"] == asset_name + ".sig":
            signature_asset = asset

    if update_asset is None:

        raise RuntimeError(
            f"Yeni sürüm bulundu ({latest_version}) fakat "
            f"{asset_name} bulunamadı."
        )

    if signature_asset is None:

        raise RuntimeError(
            f"Yeni sürüm bulundu ({latest_version}) fakat "
            f"{asset_name}.sig bulunamadı."
        )

    return {
        "version": latest_version,

        "url": update_asset[
            "browser_download_url"
        ],

        "signature_url": signature_asset[
            "browser_download_url"
        ],

        "name": asset_name,
    }


def download_file(
    url,
    destination,
    progress_callback=None
):

    destination = Path(destination)
    temporary_file = destination.with_suffix(
        destination.suffix + ".tmp"
    )

    try:
        with requests.get(
            url,
            stream=True,
            verify=False,
            timeout=30
        ) as response:

            response.raise_for_status()

            total_size = int(
                response.headers.get(
                    "content-length",
                    0
                )
            )

            downloaded = 0

            with open(
                temporary_file,
                "wb"
            ) as file:

                for chunk in response.iter_content(
                    chunk_size=1024 * 1024
                ):

                    if not chunk:
                        continue

                    file.write(chunk)
                    downloaded += len(chunk)

                    if (
                        progress_callback is not None
                        and total_size > 0
                    ):
                        progress = (
                            downloaded / total_size
                        ) * 100

                        progress_callback(progress)

        os.replace(
            temporary_file,
            destination
        )

    except Exception:

        if temporary_file.exists():
            temporary_file.unlink()

        raise

def calculate_sha256(path):

    sha256 = hashlib.sha256()

    with open(
        path,
        "rb"
    ) as file:

        while chunk := file.read(
            1024 * 1024
        ):

            sha256.update(chunk)

    return sha256.digest()


def verify_update():

    if not os.path.isfile(
        PUBLIC_KEY_FILE
    ):
        raise RuntimeError(
            "Public key bulunamadı."
        )

    if not os.path.isfile(
        UPDATE_ZIP
    ):
        raise RuntimeError(
            "Güncelleme ZIP'i bulunamadı."
        )

    if not os.path.isfile(
        SIGNATURE_FILE
    ):
        raise RuntimeError(
            "Güncelleme imzası bulunamadı."
        )

    with open(
        PUBLIC_KEY_FILE,
        "rb"
    ) as file:

        public_key = (
            serialization.load_pem_public_key(
                file.read()
            )
        )

    file_hash = calculate_sha256(
        UPDATE_ZIP
    )

    with open(
        SIGNATURE_FILE,
        "rb"
    ) as file:

        signature = file.read()

    try:

        public_key.verify(
            signature,
            file_hash
        )

    except InvalidSignature:

        raise RuntimeError(
            "Güncelleme imzası geçersiz! "
            "Güncelleme reddedildi."
        )

    return True


def prepare_update(url, signature_url, progress_callback=None):
    try:
        # Eski güncelleme dosyalarını temizle
        if UPDATE_DIR.exists():
            shutil.rmtree(UPDATE_DIR)

        UPDATE_FILES_DIR.mkdir(parents=True, exist_ok=True)

        # ZIP'i indir
        download_file(
            url,
            UPDATE_ZIP,
            progress_callback
        )

        # Dijital imzayı indir
        download_file(
            signature_url,
            SIGNATURE_FILE
        )

        # Dijital imzayı doğrula
        verify_update()

        # Doğrulama başarılıysa ZIP'i aç
        with zipfile.ZipFile(UPDATE_ZIP, "r") as zip_file:
            zip_file.extractall(UPDATE_FILES_DIR)

        # Geçici dosyaları sil
        UPDATE_ZIP.unlink()
        SIGNATURE_FILE.unlink()

        if progress_callback:
            progress_callback(100)

        return True, None

    except InvalidSignature:
        shutil.rmtree(UPDATE_DIR, ignore_errors=True)

        return (
            False,
            "Güncelleme hatası: Güncellemenin doğrulaması başarısız oldu."
        )

    except requests.RequestException:
        shutil.rmtree(UPDATE_DIR, ignore_errors=True)

        return (
            False,
            "Güncelleme hatası: Güncelleme indirilemedi."
        )

    except zipfile.BadZipFile:
        shutil.rmtree(UPDATE_DIR, ignore_errors=True)

        return (
            False,
            "Güncelleme hatası: Güncelleme dosyası bozuk."
        )

    except Exception:
        shutil.rmtree(UPDATE_DIR, ignore_errors=True)

        return (
            False,
            "Güncelleme hatası: Beklenmeyen bir hata oluştu."
        )


def apply_pending_update():
    if not UPDATE_FILES_DIR.exists():
        return

    protected_files = {
        "achievements.dat",
        "device_data.dat",
        "settings.json",
    }

    protected_directories = {
        "saves",
    }

    game_dir = Path(GAME_DIR)

    for source in UPDATE_FILES_DIR.rglob("*"):

        if not source.is_file():
            continue

        relative_path = source.relative_to(UPDATE_FILES_DIR)

        # Korunan klasörün içindeyse atla
        if any(
            part in protected_directories
            for part in relative_path.parts
        ):
            continue

        # Korunan dosyaysa atla
        if relative_path.name in protected_files:
            continue

        destination = game_dir / relative_path

        destination.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        shutil.copy2(
            source,
            destination
        )

    shutil.rmtree(
        UPDATE_DIR,
        ignore_errors=True
    )