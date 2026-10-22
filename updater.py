import os
import sys
import time
import shutil
import threading
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import ttk

# Korunan öğeler
PROTECTED_FILES = {
    "achievements.dat",
    "device_data.dat",
    "settings.json",
}

PROTECTED_DIRECTORIES = {
    "saves",
}


def wait_and_copy(source: Path, destination: Path, max_retries: int = 20, delay: float = 0.5):
    destination.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(max_retries):
        try:
            shutil.copy2(source, destination)
            return True
        except PermissionError:
            time.sleep(delay)
        except Exception:
            time.sleep(delay)
    return False


class UpdateApp:
    def __init__(self, root, update_files_dir, game_dir, update_dir, relaunch_exe):
        self.root = root
        self.update_files_dir = Path(update_files_dir)
        self.game_dir = Path(game_dir)
        self.update_dir = Path(update_dir)
        self.relaunch_exe = relaunch_exe

        # Pencere Tasarımı
        self.root.title("Oyun Güncelleniyor")
        self.root.geometry("380x140")
        self.root.resizable(False, False)

        # Ekranın ortasına yerleştir
        self.center_window(380, 140)

        # Etiketler ve İlerleme Çubuğu
        self.status_label = tk.Label(
            root,
            text="Güncelleme hazırlanıyor...",
            font=("Segoe UI", 10, "bold")
        )
        self.status_label.pack(pady=(20, 8))

        self.progress_bar = ttk.Progressbar(
            root,
            orient="horizontal",
            length=320,
            mode="determinate"
        )
        self.progress_bar.pack(pady=5)

        self.detail_label = tk.Label(
            root,
            text="Lütfen bekleyin...",
            font=("Segoe UI", 8),
            fg="#555555"
        )
        self.detail_label.pack(pady=(4, 0))

        # Güncelleme işlemini arka plan iş parçacığında başlat
        threading.Thread(target=self.run_update, daemon=True).start()

    def center_window(self, width, height):
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def run_update(self):
        # 1. Ana oyunun dosya kilidini bırakması için kısa bekleme
        time.sleep(1.2)

        if not self.update_files_dir.exists():
            self.finish()
            return

        # Kopyalanacak dosyaları listele ve filtrele
        all_files = []
        for source in self.update_files_dir.rglob("*"):
            if not source.is_file():
                continue

            rel = source.relative_to(self.update_files_dir)
            if any(part in PROTECTED_DIRECTORIES for part in rel.parts):
                continue
            if rel.name in PROTECTED_FILES:
                continue

            all_files.append((source, rel))

        total_files = len(all_files)
        if total_files > 0:
            self.root.after(0, lambda: self.progress_bar.config(maximum=total_files))

        # 2. Dosyaları kopyala ve arayüzü güncelle
        for idx, (source, rel) in enumerate(all_files, start=1):
            dest = self.game_dir / rel

            # Arayüz metnini güncelle
            self.root.after(
                0,
                lambda r=rel.name, i=idx: self.update_status(f"Kopyalanıyor: {r}", i)
            )

            wait_and_copy(source, dest)

        # 3. Geçici güncelleme klasörünü sil
        self.root.after(0, lambda: self.status_label.config(text="Temizleniyor..."))
        shutil.rmtree(self.update_dir, ignore_errors=True)

        # 4. Tamamlandı ve oyunu başlat
        self.finish()

    def update_status(self, text, current_step):
        self.status_label.config(text="Dosyalar Güncelleniyor...")
        self.detail_label.config(text=text)
        self.progress_bar["value"] = current_step

    def finish(self):
        # Güncellenen oyunu yeniden başlat
        if os.path.exists(self.relaunch_exe):
            subprocess.Popen([self.relaunch_exe])

        # Pencereyi kapat ve süreci sonlandır
        self.root.after(200, self.root.destroy)


def main():
    if len(sys.argv) < 5:
        sys.exit(1)

    root = tk.Tk()
    UpdateApp(
        root=root,
        update_files_dir=sys.argv[1],
        game_dir=sys.argv[2],
        update_dir=sys.argv[3],
        relaunch_exe=sys.argv[4]
    )
    root.mainloop()


if __name__ == "__main__":
    main()