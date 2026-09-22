import os
import platform
import shutil
import tempfile
import zipfile
from basedir import BASE_DIR as GAME_DIR

import requests
from packaging.version import Version

from version import VERSION


GITHUB_API = (
    "https://api.github.com/repos/"
    "LastHope48/savas-oyunu-1/releases/latest"
)


UPDATE_DIR = os.path.join(GAME_DIR, "_update")
UPDATE_ZIP = os.path.join(UPDATE_DIR, "update.zip")


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
            f"Desteklenmeyen işletim sistemi: {platform.system()}"
        )

    for asset in release["assets"]:

        if asset["name"] == asset_name:

            return {
                "version": latest_version,
                "url": asset["browser_download_url"],
                "name": asset["name"],
            }

    raise RuntimeError(
        f"Yeni sürüm bulundu ({latest_version}) fakat "
        f"{asset_name} bulunamadı."
    )


def download_update(url, progress_callback=None):
    os.makedirs(UPDATE_DIR, exist_ok=True)

    temporary_zip = UPDATE_ZIP + ".tmp"

    try:
        with requests.get(
            url,
            stream=True,
            timeout=30
        ) as response:

            response.raise_for_status()

            total_size = int(
                response.headers.get("content-length", 0)
            )

            downloaded = 0

            with open(temporary_zip, "wb") as file:

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
            temporary_zip,
            UPDATE_ZIP
        )

        return True

    except Exception:

        if os.path.exists(temporary_zip):
            os.remove(temporary_zip)

        raise



def prepare_update(
    url,
    progress_callback=None
):

    """
    ZIP'i indirir ve _update klasörüne çıkarır.
    Gerçek güncelleme henüz yapılmaz.
    """

    if os.path.exists(UPDATE_DIR):
        shutil.rmtree(UPDATE_DIR)

    os.makedirs(UPDATE_DIR)

    download_update(
        url,
        progress_callback
    )

    extract_dir = os.path.join(
        UPDATE_DIR,
        "files"
    )

    os.makedirs(extract_dir)

    with zipfile.ZipFile(
        UPDATE_ZIP,
        "r"
    ) as zip_file:

        zip_file.extractall(
            extract_dir
        )

    os.remove(UPDATE_ZIP)

    if progress_callback is not None:
        progress_callback(100)

    return True



UPDATE_DIR = os.path.join(GAME_DIR, "_update")
UPDATE_FILES_DIR = os.path.join(UPDATE_DIR, "files")


def apply_pending_update():
    if not os.path.isdir(UPDATE_FILES_DIR):
        return False

    try:
        for name in os.listdir(UPDATE_FILES_DIR):
            source = os.path.join(UPDATE_FILES_DIR, name)
            destination = os.path.join(GAME_DIR, name)

            if os.path.isdir(source):
                shutil.copytree(
                    source,
                    destination,
                    dirs_exist_ok=True
                )
            else:
                shutil.copy2(source, destination)

        # Güncelleme başarıyla uygulandıysa klasörü tamamen sil
        shutil.rmtree(UPDATE_DIR)

        return True

    except Exception as e:
        print(f"Güncelleme uygulanamadı: {e}")
        return False