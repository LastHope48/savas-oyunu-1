import os
import platform
import shutil
import zipfile
import hashlib

from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

from basedir import BASE_DIR as GAME_DIR

import requests
from packaging.version import Version

from version import VERSION


GITHUB_API = (
    "https://api.github.com/repos/"
    "LastHope48/savas-oyunu-1/releases/latest"
)


UPDATE_DIR = os.path.join(
    GAME_DIR,
    "_update"
)

UPDATE_ZIP = os.path.join(
    UPDATE_DIR,
    "update.zip"
)

UPDATE_FILES_DIR = os.path.join(
    UPDATE_DIR,
    "files"
)

SIGNATURE_FILE = os.path.join(
    UPDATE_DIR,
    "update.zip.sig"
)

PUBLIC_KEY_FILE = os.path.join(
    GAME_DIR,
    "public_key.pem"
)


def get_latest_release():

    response = requests.get(
        GITHUB_API,
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

    temporary_file = destination + ".tmp"

    try:

        with requests.get(
            url,
            stream=True,
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

                        progress_callback(
                            progress
                        )

        os.replace(
            temporary_file,
            destination
        )

    except Exception:

        if os.path.exists(temporary_file):
            os.remove(temporary_file)

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


def prepare_update(
    url,
    signature_url,
    progress_callback=None
):

    """
    ZIP'i ve dijital imzasını indirir.

    Daha sonra ZIP'in SHA-256 hash'ini hesaplar
    ve dijital imzayı public key ile doğrular.

    Doğrulama başarısız olursa ZIP çıkarılmaz.
    """

    if os.path.exists(
        UPDATE_DIR
    ):

        shutil.rmtree(
            UPDATE_DIR
        )

    os.makedirs(
        UPDATE_DIR
    )

    download_file(
        url,
        UPDATE_ZIP,
        progress_callback
    )

    download_file(
        signature_url,
        SIGNATURE_FILE
    )

    verify_update()

    os.makedirs(
        UPDATE_FILES_DIR
    )

    with zipfile.ZipFile(
        UPDATE_ZIP,
        "r"
    ) as zip_file:

        zip_file.extractall(
            UPDATE_FILES_DIR
        )

    os.remove(
        UPDATE_ZIP
    )

    os.remove(
        SIGNATURE_FILE
    )

    if progress_callback is not None:
        progress_callback(
            100
        )

    return True


def apply_pending_update():

    if not os.path.isdir(
        UPDATE_FILES_DIR
    ):
        return False

    try:

        for name in os.listdir(
            UPDATE_FILES_DIR
        ):

            source = os.path.join(
                UPDATE_FILES_DIR,
                name
            )

            destination = os.path.join(
                GAME_DIR,
                name
            )

            if os.path.isdir(
                source
            ):

                shutil.copytree(
                    source,
                    destination,
                    dirs_exist_ok=True
                )

            else:

                shutil.copy2(
                    source,
                    destination
                )

        shutil.rmtree(
            UPDATE_DIR
        )

        return True

    except Exception as e:

        print(
            f"Güncelleme uygulanamadı: {e}"
        )

        return False
