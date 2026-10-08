import json
import os
import math
import requests
import pygame
from basedir import BASE_DIR
from device_id import DeviceID
from lang_support import Lang

DEBUG = False
DOMAIN = r"api.infinitesoft-tr.com"

# Çoklu dil destekli başlık etiketi
POPUP_HEADER_LANG = Lang(
    türkçe="BAŞARI AÇILDI!",
    english="ACHIEVEMENT UNLOCKED!",
    arabic="تم فتح الإنجاز!",
    sanskrit="उपलब्धिः उद्घाटिता!"
)


class AchievementPopup:
    """Sağ alt köşeden yumuşakça kayarak çıkan ve kaybolan başarı kutucuğu."""
    WIDTH = 340
    HEIGHT = 76
    BOTTOM_OFFSET = 120  # Ekranın altından ne kadar yukarıda duracağı

    def __init__(self, metadata: dict, current_lang: str = "türkçe"):
        self.metadata = metadata
        self.current_lang = current_lang
        
        # Görseli kutuya uygun boyuta ölçekle (60x60)
        orig_img = metadata.get("image")
        if orig_img:
            self.image = pygame.transform.smoothscale(orig_img, (56, 56))
        else:
            self.image = None

        # Durumlar: 'in' (giriş), 'stay' (bekleme), 'out' (çıkış), 'done' (bitti)
        self.state = "in"
        self.timer = 0.0
        self.stay_duration = 3.2  # Ekranda kalma süresi (saniye)

        # X koordinatları (Ekran dışından başlar)
        self.x = 9999.0
        self.y = 0.0
        self.target_x = 0.0

        # Yazı Tipleri (Varsayılan sistem fontları)
        self.font_header = pygame.font.SysFont("Arial", 13, bold=True)
        self.font_title = pygame.font.SysFont("Arial", 17, bold=True)

    def _get_text(self, item) -> str:
        if isinstance(item, Lang):
            return getattr(item, self.current_lang, getattr(item, "türkçe", str(item)))
        return str(item)

    def update(self, dt: float, swidth: int, sheight: int):
        self.target_x = swidth - self.WIDTH
        self.y = sheight - self.BOTTOM_OFFSET

        # İlk karede ekranın tam dışına yerleştir
        if self.x > swidth:
            self.x = float(swidth)

        if self.state == "in":
            # Hedefe doğru yumuşak ivmelenme (Easing Lerp)
            self.x += (self.target_x - self.x) * min(1.0, 10.0 * dt)
            if abs(self.x - self.target_x) < 1.0:
                self.x = self.target_x
                self.state = "stay"

        elif self.state == "stay":
            self.timer += dt
            if self.timer >= self.stay_duration:
                self.state = "out"

        elif self.state == "out":
            # Sağa doğru hızlanarak çıkış
            exit_speed = max(400.0, (self.x - self.target_x + 50.0) * 8.0)
            self.x += exit_speed * dt
            if self.x >= swidth + 20:
                self.state = "done"

    def draw(self, surface: pygame.Surface):
        if self.state == "done":
            return

        rect = pygame.Rect(int(self.x), int(self.y), self.WIDTH, self.HEIGHT)

        # 1. Arka Plan Kutusu (Sadece sol köşeleri yuvarlak)
        pygame.draw.rect(
            surface,
            (24, 25, 30),
            rect,
            border_top_left_radius=18,
            border_bottom_left_radius=18,
            border_top_right_radius=0,
            border_bottom_right_radius=0
        )

        # 2. Vurgulu Sol Kenarlık (Altın Sarısı Çizgi)
        pygame.draw.rect(
            surface,
            (218, 165, 32),
            rect,
            width=2,
            border_top_left_radius=18,
            border_bottom_left_radius=18,
            border_top_right_radius=0,
            border_bottom_right_radius=0
        )

        # 3. Başarı Görseli
        if self.image:
            img_rect = self.image.get_rect(midleft=(rect.left + 12, rect.centery))
            surface.blit(self.image, img_rect)
            text_start_x = img_rect.right + 14
        else:
            text_start_x = rect.left + 16

        # 4. 'BAŞARI AÇILDI!' Yazısı (Küçük Sarı / Altın)
        header_str = self._get_text(POPUP_HEADER_LANG)
        header_surf = self.font_header.render(header_str, True, (255, 215, 0))
        surface.blit(header_surf, (text_start_x, rect.top + 15))

        # 5. Başarı Başlığı (Beyaz ve Net)
        title_str = self._get_text(self.metadata.get("title", ""))
        title_surf = self.font_title.render(title_str, True, (245, 245, 245))
        surface.blit(title_surf, (text_start_x, rect.top + 36))


class Achievements:
    FILE = os.path.join(BASE_DIR, "achievements.dat")

    def __init__(self, device: DeviceID):
        self.device = device
        self.illegal = False
        self.popup_queue: list[AchievementPopup] = []
        self.current_popup: AchievementPopup | None = None

        self.achievements = {
            "win": {"unlocked": False, "hmac": None},
            "500_kill": {"unlocked": False, "hmac": None},
            "10_000_kill": {"unlocked": False, "hmac": None},
            "1_000_000_kill": {"unlocked": False, "hmac": None},
            "masks_importance": {"unlocked": False, "hmac": None}
        }

        self.achievements_metadata: dict[str, dict[str, Lang | str]] = {
            "win": {
                "title": Lang(türkçe="Kazandın!", english="You Won!", arabic="لقد فزت.", sanskrit="त्वं जितवान्!"),
                "description": Lang(türkçe="Tebrikler, zorlu mücadelelerden sonra oyunu kazandın!", english="Congrulations, after having difficult challanges you won the game!", arabic="تهانينا، لقد فزت باللعبة بعد معارك ضارية!", sanskrit="अभिनन्दनम्, कठिनयुद्धानां अनन्तरं भवन्तः क्रीडां जितवन्तः!"),
                "image": pygame.image.load(os.path.join(BASE_DIR, r"images/crown.png"))
            },
            "500_kill": {
                "title": Lang(türkçe="500 Öldürme", english="500 Kill", arabic="500 عملية قتل", sanskrit="५०० मारयति"),
                "description": Lang(türkçe="500 Öldürme mi? Daha yolun başındasın.", english="500 Kill? You're still in the beginning of the road.", arabic="500 عملية قتل؟ أنتَ لا تزال في البداية فقط.", sanskrit="५०० मारयति ? त्वं केवलं आरभसे एव।"),
                "image": pygame.image.load(os.path.join(BASE_DIR, r"images/skull_1.png"))
            },
            "10_000_kill": {
                "title": Lang(türkçe="10000 Öldürme", english="10000 Kill", arabic="10000 عملية قتل", sanskrit="१०,००० किल्स्"),
                "description": Lang(türkçe="Vay, vay, vay. 10000 Öldürme gerçekten fazla. Peki ya daha fazlası varsa...", english="Well, well, well. 10000 Kill is really much. What about there is more...", arabic="يا للروعة! 10,000 عملية قتل هو عدد كبير حقاً. ولكن ماذا لو كان هناك المزيد...", sanskrit="वाह, वाह, वाह। १०,००० किल्स् वस्तुतः बहु अस्ति। परन्तु यदि तस्मात् अपि अधिकं भवति तर्हि किम्..."),
                "image": pygame.image.load(os.path.join(BASE_DIR, r"images/skull_2.png"))
            },
            "1_000_000_kill": {
                "title": Lang(türkçe="1000000 Öldürme", english="1000000 Kill", arabic="1000000 عملية قتل", sanskrit="१,०००,००० किल्स्"),
                "description": Lang(türkçe="1000000... 1000 kere Undertale'da Genocide yapmış biri bu kadar öldürmemiştir.", english="1000000... A human beated Undertile Genocide run 1000 times wouldn't kill this many monster.", arabic='مليون... حتى الشخص الذي لعب مسار "الإبادة الجماعية" (Genocide run) في لعبة Undertale ألف مرة لم يقتل هذا العدد من الأشخاص.', sanskrit="१,०००,०००... यः कोऽपि अण्डरटेल् इत्यस्मिन् १,००० वारं Genocide run कृतवान् अपि तावत् जनान् न मारितवान्।"),
                "image": pygame.image.load(os.path.join(BASE_DIR, r"images/skull_3.png"))
            },
            "masks_importance": {
                "title": Lang(türkçe="Maskenin Önemi", english="Mask's importance", arabic="أهمية الكمامة", sanskrit="मुखौटस्य महत्त्वम्"),
                "description": Lang(türkçe="Çok yaşa Uras", english="Bless you, Uras", arabic="بارك الله فيك يا أوراس.", sanskrit="आशीर्वादं ददातु उरसः।"),
                "image": pygame.image.load(os.path.join(BASE_DIR, r"images/maske.png"))
            }
        }

        try:
            self.load()
        except (ValueError, FileNotFoundError):
            self.illegal = True

    def trigger_popup(self, achievement_id: str, lang: str = "türkçe"):
        """Başarı açıldığında ekranda kutunun belirmesini tetikler."""
        meta = self.achievements_metadata.get(achievement_id)
        if meta:
            self.popup_queue.append(AchievementPopup(meta, current_lang=lang))

    def update_popups(self, dt: float, swidth: int, sheight: int):
        """Her karede çağrılmalıdır."""
        if self.current_popup is None:
            if self.popup_queue:
                self.current_popup = self.popup_queue.pop(0)

        if self.current_popup is not None:
            self.current_popup.update(dt, swidth, sheight)
            if self.current_popup.state == "done":
                self.current_popup = None

    def draw_popups(self, surface: pygame.Surface):
        """Her karede ekranın üzerine çizilmelidir."""
        if self.current_popup is not None:
            self.current_popup.draw(surface)

    def load(self):
        if not os.path.exists(self.FILE):
            self.save()
            return
        with open(self.FILE, "r", encoding="utf-8") as f:
            self.achievements = json.load(f)

    def save(self):
        with open(self.FILE, "w", encoding="utf-8") as f:
            json.dump(self.achievements, f, indent=4)

    def unlock(self, achievement_id, lang: str = "türkçe"):
        # Eğer zaten açıksa tekrar API'ye gitme veya bildirim çıkarma
        if self.achievements.get(achievement_id, {}).get("unlocked", False):
            return True

        url = (
            "http://api.localhost:5000/achievements/unlock"
            if DEBUG
            else f"https://{DOMAIN}/achievements/unlock"
        )

        try:
            response = requests.post(
                url,
                json={
                    "achievement_id": achievement_id,
                    "device_id": self.device.device_id
                },
                timeout=10,
                verify=False
            )
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            print("API'ye ulaşılamadı:", repr(e))
            return False
        except Exception as e:
            print("UNLOCK BEKLENMEYEN HATA:", repr(e))
            raise

        if response.status_code != 200:
            return False

        data = response.json()
        self.achievements[achievement_id]["unlocked"] = True
        self.achievements[achievement_id]["hmac"] = data["hmac"]
        self.save()

        # Bildirimi kuyruğa al ve animasyonu başlat
        self.trigger_popup(achievement_id, lang=lang)

        print("ACHIEVEMENT UNLOCKED:", achievement_id)
        return True

    def verify(self, achievement_id):
        achievement = self.achievements.get(achievement_id)
        if achievement is None or not achievement["unlocked"]:
            return False

        try:
            response = requests.post(
                f"https://{DOMAIN}/achievements/verify",
                json={
                    "achievement_id": achievement_id,
                    "device_id": self.device.device_id,
                    "hmac": achievement["hmac"]
                },
                timeout=10,
                verify=False
            )
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            print("API bağlantı hatası:", repr(e))
            return None
        except Exception as e:
            print("API'de beklenmeyen hata:", repr(e))
            raise

        if response.status_code != 200:
            return False

        return response.json()["valid"]

    def is_online(self):
        try:
            response = requests.get(
                "http://api.localhost:5000/health" if DEBUG else f"https://{DOMAIN}/health",
                timeout=10,
                verify=False
            )
            return response.status_code == 200
        except Exception:
            return False