import pygame
import colours


class BarElement:
    def __init__(self, surface, on_click=None, update=None, manual_update=False):
        self.surface = surface
        self.on_click = on_click
        self.update_function = update
        self.manual_update = manual_update
        self.rect = pygame.Rect(0, 0, 0, 0)

    def update(self, manual_update=False, *args, **kwargs):
        if self.update_function:

            if self.manual_update and manual_update:
                self.surface = self.update_function(*args, **kwargs)

            elif not self.manual_update:
                self.surface = self.update_function(*args, **kwargs)


    def draw(self, surface, rect):
        self.rect = rect
    
        image_rect = self.surface.get_rect(
            center=rect.center
        )

        surface.blit(
            self.surface,
            image_rect
        )

    def handle_event(self, event: pygame.event.Event):
        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        ):
            if self.on_click:
                self.on_click()


class Bar:
    def __init__(
        self,
        x,
        y,
        w,
        h,
        color,
        *elements,
        padding=10,
        separator=True,
        image=None
    ):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = color
        self.elements: list[BarElement] = elements
        self.image: pygame.Surface | None = image

        if self.image is not None:
            self.image = pygame.transform.scale(self.image, (self.rect.width, self.rect.height))

        self.padding = padding
        self.separator = separator

    def draw(self, surface: pygame.Surface):
        if self.image is None:

            # Ana bar
            pygame.draw.rect(
                surface,
                self.color,
                self.rect
            )

            # Kenarlık
            pygame.draw.rect(
                surface,
                colours.darker(self.color, 30),
                self.rect,
                5
            )

        else:
            surface.blit(
                self.image,
                self.rect
            )

        if not self.elements:
            return

        element_width = self._per_width_for_element()

        for i, element in enumerate(self.elements):

            element_rect = pygame.Rect(
                self.rect.left + i * element_width,
                self.rect.top,
                element_width,
                self.rect.height
            )

            # Element
            element.draw(
                surface,
                element_rect
            )

            # Ayırıcı
            if self.separator and i < len(self.elements) - 1:
                x = element_rect.right

                pygame.draw.line(
                    surface,
                    colours.darker(self.color, 80),
                    (x, self.rect.top + self.padding),
                    (x, self.rect.bottom - self.padding),
                    3
                )
        

    def handle_event(self, event: pygame.event.Event):
        for element in self.elements:
            element.handle_event(event)

    def update(self, manual=False):
        for element in self.elements:
            element.update(manual)

    def _per_width_for_element(self):
        return self.rect.width // len(self.elements)
