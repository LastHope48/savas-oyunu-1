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
    GAME_DIR = Path(sys.executable).parent
    # PyInstaller 6 onedir modunda sys._MEIPASS doğrudan _internal klasörünü işaret eder:
    INTERNAL_DIR = Path(getattr(sys, "_MEIPASS", GAME_DIR / "_internal"))
else:
    GAME_DIR = Path(__file__).resolve().parent
    INTERNAL_DIR = GAME_DIR

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
        # 1. İNDİRME BAŞLAMADAN ÖNCE KRİTİK KONTROLLER (Sonradan sürpriz yaşanmasın)
        if not PUBLIC_KEY_FILE.exists():
            return False, f"Güncelleme hatası: Public key bulunamadı ({PUBLIC_KEY_FILE.name})"

        # Eski güncelleme kalıntılarını temizle
        if UPDATE_DIR.exists():
            try:
                shutil.rmtree(UPDATE_DIR)
            except PermissionError:
                return False, "Güncelleme hatası: Eski dosyalar silinemedi (Yönetici izni gerekebilir)."

        UPDATE_FILES_DIR.mkdir(parents=True, exist_ok=True)

        # 2. İNDİRME İŞLEMLERİ
        download_file(url, UPDATE_ZIP, progress_callback)
        download_file(signature_url, SIGNATURE_FILE)

        # 3. İMZA DOĞRULAMA
        verify_update()

        # 4. ARŞİVİ AÇMA
        with zipfile.ZipFile(UPDATE_ZIP, "r") as zip_file:
            zip_file.extractall(UPDATE_FILES_DIR)

        # Geçici dosyaları temizle
        UPDATE_ZIP.unlink(missing_ok=True)
        SIGNATURE_FILE.unlink(missing_ok=True)

        if progress_callback:
            progress_callback(100)

        return True, None

    # --- ÖZEL HATA YAKALAMA BLOKLARI (Son except'e düşmeyi önler) ---

    except InvalidSignature:
        shutil.rmtree(UPDATE_DIR, ignore_errors=True)
        return False, "Güncelleme hatası: Dijital imza geçersiz (Güvenlik doğrulaması başarısız)."

    except requests.RequestException as e:
        shutil.rmtree(UPDATE_DIR, ignore_errors=True)
        return False, f"Güncelleme hatası: İndirme başarısız (İnternet bağlantınızı kontrol edin)."

    except zipfile.BadZipFile:
        shutil.rmtree(UPDATE_DIR, ignore_errors=True)
        return False, f"Güncelleme hatası: İndirilen güncelleme dosyası bozuk veya eksik."

    except RuntimeError as e:
        shutil.rmtree(UPDATE_DIR, ignore_errors=True)
        return False, f"Güncelleme hatası: {e}"

    except PermissionError:
        shutil.rmtree(UPDATE_DIR, ignore_errors=True)
        return False, f"Güncelleme hatası: Dosya yazma izni yok (Akıllı tahta koruması aktif olabilir)."

    except Exception as e:
        # Gerçekten öngörülemeyen nadir bir şey olursa en azından hatayı logla ve gizleme
        shutil.rmtree(UPDATE_DIR, ignore_errors=True)
        print(f"KRİTİK HATA DETAYI: {type(e).__name__} - {e}")
        return False, f"Güncelleme hatası [{type(e).__name__}]: {e}"


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