import os
import json
import logging
import importlib.util
from pathlib import Path
import pygame

from basedir import BASE_DIR
import levels
from screens.types import ScreenType


class ModInfo:
    def __init__(self, folder_path: Path, meta: dict):
        self.folder_path = folder_path
        self.id = meta.get("id", folder_path.name)
        self.name = meta.get("name", folder_path.name)
        self.version = meta.get("version", "1.0.0")
        self.author = meta.get("author", "Bilinmiyor")
        self.description = meta.get("description", "Açıklama yok.")
        self.enabled = meta.get("enabled", True)

        # İkon yükleme
        self.icon_surf = None
        icon_path = folder_path / "icon.png"
        if icon_path.exists():
            try:
                raw_icon = pygame.image.load(str(icon_path)).convert_alpha()
                self.icon_surf = pygame.transform.smoothscale(raw_icon, (64, 64))
            except Exception:
                pass


class ModAPI:
    """Mod geliştiricilerine sunulan güvenli fonksiyon kütüphanesi."""
    def __init__(self, game, mod_info: ModInfo):
        self.game = game
        self.mod_info = mod_info

    # ---------------------------------------------------------
    # 1. DÜNYA SEÇİM EKRANINA DÜNYA EKLEME
    # ---------------------------------------------------------
    def register_world(self, cassette_world):
        """WorldSelectScreen'e yeni bir kaset/dünya ekler."""
        try:
            if hasattr(self.game, "mod_manager"):
                self.game.mod_manager.custom_worlds.append(cassette_world)
                logging.info(f"[{self.mod_info.name}] Kaset havuza kaydedildi: {cassette_world.title}")
                print(f"[MOD] Yeni kaset yüklendi: {cassette_world.title}")
        except Exception as e:
            logging.error(f"[{self.mod_info.name}] register_world hatası: {e}")

    # ---------------------------------------------------------
    # 2. SEVİYE SİLAHI VE İTEM SÖZLÜKLERİNE MÜDAHALE
    # ---------------------------------------------------------
    def register_level_sword(self, level_key: str, sword_obj):
        """Örn: level_key='level8', sword_obj=PlazmaKilic"""
        levels.level_sword_map[level_key] = sword_obj
        logging.info(f"[{self.mod_info.name}] {level_key} kılıcı güncellendi.")

    def register_level_items(self, level_key: str, item_list: list):
        """Örn: level_key='level5', item_list=[Item(...)]"""
        if level_key not in levels.level_item_map:
            levels.level_item_map[level_key] = []
        levels.level_item_map[level_key].extend(item_list)

    def register_level_enemies(self, level_index: int, enemy_list: list):
        """Mevcut bir seviyeye fazladan düşman enjekte eder."""
        if 0 <= level_index < len(levels.levels):
            levels.levels[level_index].extend(enemy_list)

    def add_new_level(self, enemy_list: list, sword_reward=None, item_rewards=None):
        """Oyunun sonuna sıfırdan yeni bir bölüm/dalga ekler."""
        levels.levels.append(enemy_list)
        new_lvl_num = len(levels.levels)
        if sword_reward:
            levels.level_sword_map[f"level{new_lvl_num}"] = sword_reward
        if item_rewards:
            levels.level_item_map[f"level{new_lvl_num}"] = item_rewards


class ModManager:
    CONFIG_FILE = os.path.join(BASE_DIR, "mods_config.json")
    MODS_DIR = os.path.join(BASE_DIR, "mods")

    def __init__(self, game):
        self.game = game
        self.mods: dict[str, ModInfo] = {}
        self.loaded_modules = {}
        self.custom_worlds: list = []

        # mods klasörü yoksa otomatik oluştur
        Path(self.MODS_DIR).mkdir(parents=True, exist_ok=True)
        self.load_config()
        self.scan_mods()

    def scan_mods(self):
        """Klasördeki tüm modları bulur ve manifestlerini okur."""
        self.mods.clear()
        mods_path = Path(self.MODS_DIR)

        for mod_folder in mods_path.iterdir():
            if mod_folder.is_dir():
                manifest_path = mod_folder / "mod.json"
                if manifest_path.exists():
                    try:
                        with open(manifest_path, "r", encoding="utf-8") as f:
                            meta = json.load(f)
                        mod_info = ModInfo(mod_folder, meta)

                        # Config dosyasındaki açık/kapalı durumunu koru
                        if mod_info.id in self.config_states:
                            mod_info.enabled = self.config_states[mod_info.id]

                        self.mods[mod_info.id] = mod_info
                    except Exception as e:
                        logging.error(f"Mod manifesti okunamadı ({mod_folder.name}): {e}")

    def load_mods(self):
        """Aktif (enabled) olan tüm modların main.py dosyasını çalıştırır."""
        for mod_id, mod in self.mods.items():
            if not mod.enabled:
                continue

            entry_point = mod.folder_path / "main.py"
            if not entry_point.exists():
                logging.warning(f"Modun main.py dosyası yok: {mod.name}")
                continue

            try:
                spec = importlib.util.spec_from_file_location(f"mod_{mod_id}", str(entry_point))
                module = importlib.util.module_from_spec(spec)
                self.loaded_modules[mod_id] = module
                spec.loader.exec_module(module)

                # Mod içindeki init(api) veya setup(api) fonksiyonunu çağır
                api = ModAPI(self.game, mod)
                if hasattr(module, "init"):
                    module.init(api)
                elif hasattr(module, "setup"):
                    module.setup(api)

                logging.info(f"Mod başarıyla yüklendi: {mod.name} (v{mod.version})")
            except Exception as e:
                logging.error(f"Mod yüklenirken çökme oluştu [{mod.name}]: {e}")

    def toggle_mod(self, mod_id: str) -> bool:
        """Modu aktif/pasif yapar ve config dosyasına kaydeder."""
        if mod_id in self.mods:
            self.mods[mod_id].enabled = not self.mods[mod_id].enabled
            self.save_config()
            return self.mods[mod_id].enabled
        return False

    def load_config(self):
        self.config_states = {}
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                    self.config_states = json.load(f)
            except Exception:
                pass

    def save_config(self):
        states = {mod_id: mod.enabled for mod_id, mod in self.mods.items()}
        try:
            with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(states, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Mod config kaydedilemedi: {e}")