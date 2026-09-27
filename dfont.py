import pygame
import sys
from dataclasses import dataclass

pygame.init()

if __name__ == "__main__":
    screen = pygame.display.set_mode((800, 800), pygame.RESIZABLE)


def darker_color(color: tuple, amount: int):
    return tuple(max(0, c-amount) for c in color)


def split_text(text, max_chars=9):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        if len(current) + len(word) + 1 <= max_chars:
            current += (" " if current else "") + word
        else:
            lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


@dataclass
class DynamicFont:
    name: str
    min_size: int
    max_size: int

    def __post_init__(self):
        self.load(self.max_size)

    def load(self, size: int):
        try:
            self._font = pygame.font.Font(self.name, size)    
        except (FileNotFoundError, pygame.error):
            self._font = pygame.font.SysFont(self.name, size)

    def default(self):
        try:
            self._font = pygame.font.Font(self.name, self.max_size)
        except (FileNotFoundError, pygame.error):
            self._font = pygame.font.SysFont(self.name, self.max_size)

    def render_static(self, text: str, color: tuple[int, int, int] | str, breaklines: bool = False) -> pygame.Surface | list[pygame.Surface]:
        r'''
        Sabit boyutta render etmek için.

        Args:
            text: Render edeceğiniz metin
            color: Hangi renkte render edeceğiniz. Pygamede tanımlı olan string renkler veya rgb tuple kullanın.
            breaklines: ``text`` metninde olan yeni satırlarda (``\n``) satır satır yazılsın mı?
        
        Returns:
            Eğer ``breaklines`` False ise tek bir pygame.Surface objesi, True ise liste içinde her satır için ayrı bir pygame.Surface objesi.
        '''
        self.default()

        if breaklines:
            lines = text.split("\n")
            renders = []
            for line in lines:
                renders.append(
                    self._font.render(line, True, color)
                )

            return renders

        else:
            return self._font.render(text, True, color)

    def wrap_text(self, text: str, max_width: int):
        lines = []

        for paragraph in text.split("\n"):
            words = paragraph.split()

            if not words:
                lines.append("")
                continue

            current = ""

            for word in words:
                test = word if not current else f"{current} {word}"

                if self._font.size(test)[0] <= max_width:
                    current = test
                else:
                    if current:
                        lines.append(current)

                    current = word

            if current:
                lines.append(current)

        return lines


    @property
    def hsizemax(self):
        self.default()
        return self._font.get_height()

    @property
    def hsize(self):
        return self._font.get_height()

    def size(self, text: str, reset: bool = False):
        if reset:
            self.default()

        return self._font.size(text)

    def render(
        self,
        text: str,
        color: tuple[int, int, int] | str,
        surface: pygame.Surface,
        gap: int = 0,
        breaklines: bool = False
    ):
        max_width = surface.get_width() - gap
        max_height = surface.get_height() - gap

        low = self.min_size
        high = self.max_size
        best_size = self.min_size

        while low <= high:
            size = (low + high) // 2
            self.load(size)

            if breaklines:
                # ÖNEMLİ:
                # Bu font boyutunda tekrar wrap yapılıyor.
                lines = self.wrap_text(text, max_width)
            else:
                lines = [text]

            line_height = self._font.get_height()

            text_width = max(
                (self._font.size(line)[0] for line in lines),
                default=0
            )

            text_height = line_height * len(lines)

            fits = (
                text_width <= max_width
                and text_height <= max_height
            )

            if fits:
                best_size = size
                low = size + 1
            else:
                high = size - 1

        # En uygun font boyutuna dön
        self.load(best_size)

        if breaklines:
            # Burada da SON font boyutuna göre tekrar wrap
            lines = self.wrap_text(text, max_width)

            line_height = self._font.get_height()

            renders = [
                self._font.render(line, True, color)
                for line in lines
            ]

            return renders, line_height

        rendered = self._font.render(text, True, color)

        return rendered, self._font.get_height()


class MsgBox:

    def __init__(
        self,
        text: str,
        font: DynamicFont,
        width: int,
        height: int,
        x: int,
        y: int,
        color: tuple[int, int, int],
        border: int,
        padding: int = 10,
        text_color: tuple[int, int, int] | str = "black",
        typing_speed: float = 50.0
    ):
        self.text = text
        self.font = font

        self.width = width
        self.height = height

        self.x = x
        self.y = y

        self.color = color
        self.border = border
        self.padding = padding
        self.text_color = text_color

        # Saniyede kaç karakter yazılacağı
        self.typing_speed = typing_speed

        # Typewriter sistemi
        self.visible_chars = len(text)
        self.typing = False

    @property
    def rect(self):
        return pygame.Rect(
            self.x,
            self.y,
            self.width,
            self.height
        )

    @property
    def displayed_text(self):
        """Şu anda ekranda görünmesi gereken metni döndürür."""
        return self.text[:int(self.visible_chars)]

    @property
    def finished(self):
        """Yazının tamamlanıp tamamlanmadığını söyler."""
        return self.visible_chars >= len(self.text)

    def start_typing(self):
        """Metni baştan harf harf yazmaya başlatır."""
        self.visible_chars = 0
        self.typing = True

    def stop_typing(self):
        """Yazmayı durdurur ve metnin tamamını gösterir."""
        self.visible_chars = len(self.text)
        self.typing = False

    def skip_typing(self):
        """
        Yazma devam ediyorsa metni anında tamamlar.

        Örneğin oyuncu SPACE'e basınca bütün mesajın
        hemen görünmesini sağlar.
        """
        if self.typing:
            self.stop_typing()

    def update(self, dt: float):
        """
        Typewriter efektini günceller.

        dt:
            Son frame'den beri geçen süre (saniye).
        """

        if not self.typing:
            return

        self.visible_chars += self.typing_speed * dt

        if self.visible_chars >= len(self.text):
            self.visible_chars = len(self.text)
            self.typing = False

    def set_text(
        self,
        text: str,
        start_typing: bool = False
    ):
        """
        Mesajı değiştirir.

        start_typing=True verilirse yeni mesaj
        baştan yazılmaya başlar.
        """

        self.text = text

        if start_typing:
            self.start_typing()
        else:
            self.stop_typing()

    def draw(self, surface: pygame.Surface):

        rect = self.rect

        # Ana kutu
        pygame.draw.rect(
            surface,
            self.color,
            rect,
            border_radius=self.border
        )

        # Kenarlık
        pygame.draw.rect(
            surface,
            darker_color(self.color, 40),
            rect,
            width=max(1, self.height // 17),
            border_radius=self.border
        )

        # Yazı alanı
        text_area = pygame.Rect(
            rect.x + self.padding,
            rect.y + self.padding,
            rect.width - self.padding * 2,
            rect.height - self.padding * 2
        )

        # Şu anda görünmesi gereken metin
        displayed_text = self.displayed_text

        # Metni kutunun genişliğine göre satırlara böl
        rendered_texts, line_height = self.font.render(
            displayed_text,
            self.text_color,
            pygame.Surface(text_area.size),
            gap=0,
            breaklines=True
        )

        # Satırları çiz
        for i, rendered_text in enumerate(rendered_texts):

            y = text_area.y + i * line_height

            # Kutunun dışına taşmasını engelle
            if y + rendered_text.get_height() > text_area.bottom:
                break

            surface.blit(
                rendered_text,
                (
                    text_area.x,
                    y
                )
            )


if __name__ == "__main__":

    run = True

    GAME_STATE = "GAME_MODE_SELECT"
    font = DynamicFont("arial", 1, 700)

    text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.Duis vel commodo quam. Praesent aliquam metus vel elit lacinia tristique.Proin commodo bibendum dapibus. Nunc lacinia rhoncus nulla et rhoncus. Suspendisse fringilla eget elit iaculis auctor. Proin vitae enim ac nunc vulputate ultrices. Etiam hendrerit enim ac sapien pharetra consectetur. Donec imperdiet nibh tortor, in malesuada mauris finibus eget. Donec suscipit porttitor ultrices. Ut eu augue venenatis, facilisis magna vitae, bibendum nisi. Duis nec commodo ex, congue efficitur libero.\nNunc consectetur erat id nisl luctus, at tincidunt eros luctus.' * 10

    i = 1
    message = MsgBox(text, font, 2000, 2000, 50, 50, (0, 0, 255), 10, typing_speed=3000, text_color="white")
    message.start_typing()

    clock = pygame.time.Clock()

    cooldown = 0.01

    while run:
        dt = clock.tick(120) / 1000

        message.update(dt)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        if GAME_STATE == "GAME_MODE_SELECT":
            screen.fill("black")
            message.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)
