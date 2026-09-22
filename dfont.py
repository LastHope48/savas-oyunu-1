import pygame
import sys
from dataclasses import dataclass

pygame.init()

if __name__ == "__main__":
    screen = pygame.display.set_mode((800, 800))


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
        words = text.split()
        lines = []
        current = ""

        for word in words:
            test = word if not current else f"{current} {word}"

            if self.size(test)[0] <= max_width:
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

    def size(self, text: str, max: bool = True):
        if max:
            self.default()

        return self._font.size(text)

    def render(
        self,
        text: str,
        color: tuple[int, int, int] | str,
        surface: pygame.Surface,
        gap: int = 0,
        breaklines: bool = False
    ) -> tuple[list[pygame.Surface], int] | pygame.Surface:
        lines = text.split("\n") if breaklines else [text]

        low = self.min_size
        high = self.max_size
        best_size = self.min_size

        while low <= high:
            size = (low + high) // 2
            self.load(size)

            widths = [self._font.size(line)[0] for line in lines]
            line_height = self._font.get_height()

            text_width = max(widths, default=0)
            text_height = line_height * len(lines)

            fits = (
                text_width + gap <= surface.get_width()
                and text_height + gap <= surface.get_height()
            )

            if fits:
                best_size = size
                low = size + 1
            else:
                high = size - 1

        self.load(best_size)
        if breaklines:
            renders = [
                self._font.render(line, True, color)
                for line in lines
            ]
            # self.default()
            return renders, line_height

        rendered = self._font.render(text, True, color)
        # self.default()
        return rendered, line_height


class MsgBox:
    def __init__(self, text: str, font: DynamicFont, width: int, height: int, x: int, y: int, color: tuple, border: int):
        self.text = text
        self.font = font
        self.width = width
        self.height = height
        self.x = x
        self.y = y

        self.color = color
        self.border = border
        self.surface = pygame.Surface((self.width, self.height))

    def draw(self, surface: pygame.Surface):
        pygame.draw.rect(
            surface,
            self.color,
            (self.x, self.y, self.width, self.height),
            border_radius=self.border
        )

        pygame.draw.rect(
            surface,
            darker_color(self.color, 40),
            (self.x, self.y, self.width, self.height),
            width=self.height // 17,
            border_radius=self.border
        )

        padding = 10

        # Metnin kullanılabileceği alan
        text_area = pygame.Rect(
            self.x + padding,
            self.y + padding,
            self.width - padding * 2,
            self.height - padding * 2
        )

        lines = self.font.wrap_text(
            self.text,
            text_area.width
        )

        new_text = "\n".join(lines)

        rendered_texts, line_height= self.font.render(
            new_text,
            "black",
            pygame.Surface(text_area.size),
            gap=0,
            breaklines=True
        )

        for i, rendered_text in enumerate(rendered_texts):
            surface.blit(
                rendered_text,
                (
                    text_area.x,
                    text_area.y + i * line_height
                )
            )

if __name__ == "__main__":

    run = True

    GAME_STATE = "GAME_MODE_SELECT"
    font = DynamicFont("arial", 10, 70)

    text = '''
    Lorem ipsum dolor sit amet, consectetur adipiscing elit.\nDuis vel commodo quam. Praesent aliquam metus vel elit lacinia tristique.\nProin commodo bibendum dapibus. Nunc lacinia rhoncus nulla et rhoncus. Suspendisse fringilla eget elit iaculis auctor. Proin vitae enim ac nunc vulputate ultrices. Etiam hendrerit enim ac sapien pharetra consectetur. Donec imperdiet nibh tortor, in malesuada mauris finibus eget. Donec suscipit porttitor ultrices. Ut eu augue venenatis, facilisis magna vitae, bibendum nisi. Duis nec commodo ex, congue efficitur libero.\nNunc consectetur erat id nisl luctus, at tincidunt eros luctus.
    '''

    i = 1
    message = MsgBox(text, font, 600, 600, 50, 50, (0, 0, 255), 10)

    clock = pygame.time.Clock()

    cooldown = 0.01

    while run:
        dt = clock.tick(120) / 1000
        cooldown -= dt
        if cooldown <= 0:
            cooldown = 0.01
            i += 1
        message.text = text[:min(len(text), i)]
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        if GAME_STATE == "GAME_MODE_SELECT":
            screen.fill("black")
            message.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)
