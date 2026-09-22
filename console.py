import pygame
import re
import logging
import shlex
import colours
import os
from flags import SUCCESS, FAILURE


class userFont:
    fonts = []

    def __init__(self, name: str, size: int, bold=False, italic=False):
        self.name = name
        self.size = size
        self.bold = bold
        self.italic = italic
        size_name_map = {
            0: {"name": "so small", "size": "0-10"},
            1: {"name": "small", "size": "10-20"},
            2: {"name": "mid", "size": "20-30"},
            3: {"name": "big", "size": "30-40"},
            4: {"name": "so big", "size": "40-50"},
            5: {"name": "huge", "size": "50-80"},
            6: {"name": "başlık", "size": "80-160"}
        }
        for index in size_name_map.keys():
            if self.size >= int(size_name_map[index]["size"].split("-")[0]) and self.size <= int(size_name_map[index]["size"].split("-")[1]):
                self.size_name = size_name_map[index]["name"]
        if os.path.exists(name):
            self.font = pygame.font.Font(name, size)
        else:
            self.font = pygame.font.SysFont(self.name, self.size, self.bold, self.italic)
        self.fonts.append(self)

    def return_text(self, text: str, color: tuple, background: tuple = None, antialias=True):
        return self.font.render(text, antialias, color, background)

    def draw_text(self, text: str, pos: tuple, surface: pygame.Surface, color: tuple, hiza: str = None, background: tuple = None, antialias=True):
        rendered = self.return_text(text, color, background, antialias)
        if hiza is not None:
            rect = rendered.get_rect()
            if not hasattr(rect, hiza):
                raise ValueError(f"Geçersiz hiza: {hiza}")
            setattr(rect, hiza, pos)
            surface.blit(rendered, rect)
        else:
            surface.blit(rendered, pos)

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(filename)s: %(lineno)d [%(funcName)s] | %(message)s',
    level=logging.INFO,
    filename="game.log"
)


def calculate_size(initialized_size: int, initialized_screen_s: int, size: int):
    '''
    Ekran boyutuna göre boyut hesaplar. Dinamik boyut gerektiren objeler için.
    '''
    calculated = initialized_size * (size / initialized_screen_s)
    return calculated


class CommandParser:

    def __init__(self):
        self.commands = {}
        self.variables = {}

    def add_variable(self, name, value):
        self.variables[name] = value


    def add_command(self, name, action, args=None, requireds=None, success_text: str = ""):
        """
        action:
            fonksiyon veya değişken işlemi

        args:
            beklenen parametreler
        """

        if requireds is None:
            requireds=[]
            for i in range(len(args)):
                requireds.append(True)

        self.commands[name] = {
            "action": action,
            "args": args or [],
            "requireds": requireds,
            "stext": success_text
        }

    def set_main_module(self, module):
        global main_module
        main_module = module

    def run(self, text):
        parts = shlex.split(text)

        if not parts:
            return ""

        command = parts[0]
        if command == "clear":
            return ""
        values = parts[1:]


        if command not in self.commands:
            print("Bilinmeyen komut:", command)
            logging.warning(f"Unknown command: {command}")
            return FAILURE, f"Bilinmeyen Komut: {command}"


        data = self.commands[command]

        converted = []
        for i, arg_type in enumerate(data["args"]):
            required = data["requireds"][i]

            if i >= len(values):
                if required:
                    return FAILURE, f"Eksik parametre: {i + 1}. parametre gerekli."

                converted.append(None)
                continue

            try:
                converted.append(arg_type(values[i]))
            except ValueError:
                logging.warning(f"Wrong parameter. Expected {arg_type}")
                return FAILURE, f"Yanlış parametre. Parametre {i + 1} {arg_type} beklenmişti."

        
        action = data["action"]

        if callable(action):
            returned = action(*converted)
            stext = data["stext"]
            stext: str
            stext = re.sub(
            r"\[(arg\d+)\]",
            lambda m: str(converted[int(m.group(1)[3:]) - 1]),
            stext
            )
            logging.info(f"CommandParser runned successful command: {stext}")
            return returned[0], (str(returned[1]) if returned is not None else "") + "\n" + stext

        else:
            print("Geçersiz komut")
            logging.error("Invalid command.")
            return FAILURE, "Geçersiz komut."


class Console:
    def __init__(self, parser: CommandParser, font: userFont, waiting_font: userFont = None):
        self.open = False
        self.text = ""
        self.history = []
        self.parser = parser
        self.font = font
        self.waiting_font = waiting_font or font
        self.console_height = 400
        self.showing_line = 0


    def handle_event(self, event):
        event: pygame.event.Event
        if event.type == pygame.KEYDOWN:

            # Konsol aç/kapat
            if event.key == pygame.K_F1:
                self.open = not self.open
                return

            if not self.open:
                return

            # Enter
            if event.key == pygame.K_RETURN:
                if self.text:
                    self.history.append("> " + self.text)
                    if self.text == "clear":
                        self.history.clear()
                        self.text = ""
                        return
                    stext = self.parser.run(self.text)
                    print(stext)
                    exitcode = int(stext[0])
                    parts = stext[1].split("\n")
                    success_text = parts.pop(-1)
                    for part in parts:
                        self.history.append(part)
                    if exitcode == SUCCESS:
                        self.history.append(success_text)
                    elif exitcode == FAILURE:
                        self.history.append(f"FAILURE: {success_text}")
                    self.text = ""
            


            # Silme
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]


            # Yazı
            else:
                if event.unicode.isprintable():
                    self.text += event.unicode
            self.showing_line = 0
        elif event.type == pygame.MOUSEWHEEL:

            if not self.open:
                return

            # Yukarı
            if event.y > 0:
                self.showing_line += event.y

            # Aşağı
            elif event.y < 0:
                self.showing_line += event.y

            # Sınırlar
            max_history = (
                self.console_height //
                (self.font.font.get_height() + 25)
            ) * 2

            max_scroll = max(
                0,
                len(self.history) - max_history
            )

            self.showing_line = max(
                0,
                min(self.showing_line, max_scroll)
            )


    def calculate_height(self, height):
        self.console_height = int(calculate_size(400, 2160, height))
        return self.console_height

    def draw(self, screen, height):

        if not self.open:
            return

        console_height = self.calculate_height(height)
        console_y = screen.get_height() - console_height

        # arka plan
        pygame.draw.rect(
            screen,
            (20, 20, 20),
            (0, console_y, screen.get_width(), console_height)
        )

        # geçmiş yazılar
        y = console_y + 10
        max_history = console_height // (self.font.font.get_height() + 25) * 2

        end = len(self.history) - self.showing_line
        start = max(0, end - max_history)

        for line in self.history[start:end]:
            img = self.font.return_text(
                line,
                (255, 255, 255)
            )

            screen.blit(img, (10, y))
            y += 25


        # aktif komut satırı
        command_y = (
            screen.get_height()
            - self.font.font.get_height()
            - 10
        )

        rendered = self.font.return_text(
            "> " + self.text,
            colours.GREEN
        )

        screen.blit(
            rendered,
            (10, command_y)
        )

        # cursor
        cursor = self.waiting_font.return_text(
            "_",
            colours.GREEN
        )
        if (pygame.time.get_ticks() // 400) % 2 == 0:
            screen.blit(
                cursor,
                (10 + rendered.get_width(), command_y)
            )
