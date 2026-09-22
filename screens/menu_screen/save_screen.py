from .menu_screen import MenuScreen
import pygame
import colours
from classes import Slot, LimitedNumber, Button
import math
from fonts import font2, font3
from calcs import calculate_size
from screens.types import ScreenType
from lang_support import Lang

class SaveScreen(MenuScreen):
    def __init__(self, game):
        super().__init__(game)

        self.visible_slots = []
        self.page = LimitedNumber(0, 0, 1000)

        self.langs = {
            "empty_slot": Lang(türkçe="Boş Slot", english="Empty Slot"),
            "unknown_error_slot": Lang(türkçe="Bilinmeyen Hata", english="Unknown Error"),
            "corrupted_slot": Lang(türkçe="Bozuk Slot", english="Corrupted Slot"),
            "version_slot": Lang(türkçe="Sürüm", english="Version"),
            "previous": Lang(türkçe="Önceki", english="Previous"),
            "next": Lang(türkçe="Sonraki", english="Next"),
            "page": Lang(türkçe="Sayfa", english="Page")
        }

        self.sonraki_button = Button(
            0, 0, 300, 80,
            "Sonraki",
            font3,
            colours.GRAY,
            colours.WHITE,
            [ScreenType.LOAD, ScreenType.SAVE],
            colours.darker(colours.GRAY, 20),
            colours.darker(colours.GRAY, 50),
            20
        )

        self.onceki_button = Button(
            0, 0, 300, 80,
            "Önceki",
            font3,
            colours.GRAY,
            colours.WHITE,
            [ScreenType.LOAD, ScreenType.SAVE],
            colours.darker(colours.GRAY, 20),
            colours.darker(colours.GRAY, 50),
            20
        )

        self.return_button = Button(
            0, 0, 50, 50,
            "<-",
            font2,
            colours.RED,
            colours.WHITE,
            [ScreenType.LOAD, ScreenType.SAVE]
        )

    def draw(self, surface: pygame.Surface):
        surface.fill(colours.BLACK)

        slot = Slot.slots[0]

        slot_w = slot.display.width
        slot_h = slot.display.height
        gap = 20

        width = self.game.width
        height = self.game.height

        sutun_basina = max(1, (width - gap) // (slot_w + gap))
        satir_basina = max(1, (height - gap - 100) // (slot_h + gap))

        sayfa_basina = sutun_basina * satir_basina

        baslangic = self.page.deger * sayfa_basina
        bitis = min(
            baslangic + sayfa_basina,
            len(Slot.slots)
        )

        self.visible_slots.clear()

        index = baslangic

        for satir in range(satir_basina):
            for sutun in range(sutun_basina):

                if index >= bitis:
                    break

                slot: Slot = Slot.slots[index]
                self.visible_slots.append(slot)

                x = gap + sutun * (slot_w + gap)
                y = gap + satir * (slot_h + gap)

                slot.display.set_topleft(x, y)
                slot.display.text = f"Slot {slot.id + 1}"

                if slot.used:
                    slot.display.color = colours.GREEN
                    slot.display.on_mouse_color = colours.darker(
                        colours.GREEN, 20
                    )

                    slot.display.text += (
                        f"\n{slot.info['date']}"
                        f"\n{self.langs['version_slot'].get(self.game.settings.get('language'))}: {slot.info['version']}"
                    )

                elif slot.corrupted:
                    slot.display.color = colours.RED
                    slot.display.on_mouse_color = colours.RED
                    slot.display.text += f"\n{self.langs['empty_slot'].get(self.game.settings.get('language'))}"

                elif slot.unknown:
                    slot.display.color = colours.GRAY
                    slot.display.on_mouse_color = colours.GRAY
                    slot.display.text += f"\n{self.langs['unknown_error_slot'].get(self.game.settings.get('language'))}"

                else:
                    slot.display.text += f"\n{self.langs['empty_slot'].get(self.game.settings.get('language'))}"

                slot.display.draw(surface)

                index += 1

        self.onceki_button.draw(surface)
        self.sonraki_button.draw(surface)
        self.return_button.draw(surface)

        font2.draw_text(
            f"{self.page.deger + 1}. {self.langs['page'].get(self.game.settings.get('language'))}",
            (width * 0.5, height * 0.93),
            surface,
            (255, 255, 255),
            "center"
        )

    def update(self, dt):
        sayfa_basina, sayfa_sayisi = self.calculate_pages()

        self.page.max = sayfa_sayisi - 1

        width = self.game.width
        height = self.game.height

        self.return_button.set_center(width * 0.1, height * 0.93)
        self.return_button.width = calculate_size(50, 800, width)
        self.return_button.height = calculate_size(50, 800, height)

        self.onceki_button.set_center(width * 0.2, height * 0.93)
        self.onceki_button.width = calculate_size(300, 800, width)
        self.onceki_button.height = calculate_size(80, 800, height)

        self.onceki_button.text = self.langs['previous'].get(self.game.settings.get('language'))


        self.sonraki_button.set_center(width * 0.8, height * 0.93)
        self.sonraki_button.width = calculate_size(300, 800, width)
        self.sonraki_button.height = calculate_size(80, 800, height)

        self.sonraki_button.text = self.langs['next'].get(self.game.settings.get('language'))


        for button in Button.buttons:
            button.on_mouse()

    def handle_event(self, event: pygame.event.Event):
        if self.onceki_button.clicked(event, ScreenType.SAVE):
            self.change_page(-1)

        if self.sonraki_button.clicked(event, ScreenType.SAVE):
            self.change_page(1)

        if self.return_button.clicked(event, ScreenType.SAVE):
            self.game.screen_manager.set_screen(self.return_button.plus_data)

        for slot in self.visible_slots:
            slot: Slot

            if slot.display.clicked(event, ScreenType.SAVE):
                self.game.save_manager.save(
                    slot.id,
                    self.game.game_data,
                    self.game.GAME_VERSION
                )
                Slot.update_infos(self.game.save_manager)
                return

    def change_page(self, delta):
        self.page.deger += delta

    def calculate_pages(self):
        slot = Slot.slots[0]

        slot_w = slot.display.width
        slot_h = slot.display.height
        gap = 20

        width = self.game.width
        height = self.game.height

        sutun_basina = max(
            1,
            (width - gap) // (slot_w + gap)
        )

        satir_basina = max(
            1,
            (height - gap - 100) // (slot_h + gap)
        )

        sayfa_basina = sutun_basina * satir_basina

        sayfa_sayisi = max(
            1,
            math.ceil(len(Slot.slots) / sayfa_basina)
        )

        return sayfa_basina, sayfa_sayisi

    def on_enter(self, transfer_datas: dict):
        self.return_button.plus_data = transfer_datas['screen_type_before']
