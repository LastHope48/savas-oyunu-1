import os
import re
import pygame

class AnimationController:
    def __init__(
        self,
        sprites_dir: str | os.PathLike,
        speeds: dict[str, float] | None = None,
        default_speed: float = 12.0,
        target_scale: float = 1.0
    ):
        self.sprites_dir = sprites_dir
        self.target_scale = target_scale
        self.default_speed = default_speed
        self.speeds = speeds or {}
        
        # Dinamik durum sözlüğü
        self.animations: dict[str, list[pygame.Surface]] = {}
        self.load_animations()

        # İlk durumu otomatik belirle (varsa idle, yoksa bulunan ilk durum)
        if "idle" in self.animations:
            self.current_state = "idle"
        elif self.animations:
            self.current_state = next(iter(self.animations.keys()))
        else:
            self.current_state = None

        self.frame_index = 0.0

    def load_animations(self):
        if not os.path.exists(self.sprites_dir):
            return

        pattern = re.compile(r"^([a-zA-Z0-9_]+)_(\d+)\.(png|jpg|jpeg|webp)$")
        raw_files: dict[str, list[tuple[int, str]]] = {}

        # Klasördeki tüm görselleri dinamik tara
        for filename in os.listdir(self.sprites_dir):
            match = pattern.match(filename)
            if match:
                state, idx_str, _ = match.groups()
                idx = int(idx_str)
                if state not in raw_files:
                    raw_files[state] = []
                raw_files[state].append((idx, filename))

        # Kareleri indeks sırasına göre yükle
        for state, file_list in raw_files.items():
            file_list.sort(key=lambda item: item[0])
            self.animations[state] = []

            for _, filename in file_list:
                full_path = os.path.join(self.sprites_dir, filename)
                surf = pygame.image.load(full_path)
                if pygame.display.get_surface() is not None:
                    surf = surf.convert_alpha()

                if self.target_scale != 1.0:
                    new_size = (
                        int(surf.get_width() * self.target_scale),
                        int(surf.get_height() * self.target_scale)
                    )
                    surf = pygame.transform.smoothscale(surf, new_size)

                self.animations[state].append(surf)

    def update(self, new_state: str, dt: float):
        if not self.animations or new_state not in self.animations:
            return

        if self.current_state != new_state:
            self.current_state = new_state
            self.frame_index = 0.0

        frames = self.animations[self.current_state]
        if frames:
            fps = self.speeds.get(self.current_state, self.default_speed)
            self.frame_index = (self.frame_index + fps * dt) % len(frames)

    def get_frame(self, facing_left: bool = False) -> pygame.Surface | None:
            if not self.current_state or self.current_state not in self.animations:
                return None
            frames = self.animations[self.current_state]
            if not frames:
                return None
                
            cur_idx = int(self.frame_index)

            frame = frames[cur_idx]
            if facing_left:
                return pygame.transform.flip(frame, True, False)
            return frame