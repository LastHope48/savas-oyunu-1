import os
import random
import pygame
import numpy as np

class SoundPoolFX:
    def __init__(self, filepaths: list[str], volume=1.0, pitch_variations=5, pitch_range=(0.88, 1.12)):
        """
        Birden fazla ses dosyasını rastgele seçen ve her birine pitch randomization uygulayan ses havuzu.
        - filepaths: ['.wav', '.wav', ...] ses dosyası yolları listesi
        - volume: Ses seviyesi (0.0 - 1.0)
        - pitch_variations: Her bir ses için üretilecek farklı perde sayısı
        - pitch_range: Frekans değişim aralığı (0.88 daha tok/kalın, 1.12 daha tiz/keskin)
        """
        self.sound_variants = []  # [[ses1_v1, ses1_v2...], [ses2_v1, ses2_v2...]]
        self.last_played_idx = -1

        for path in filepaths:
            if not os.path.exists(path):
                print(f"[UYARI] Ses dosyası bulunamadı: {path}")
                continue

            base_sound = pygame.mixer.Sound(path)
            raw_array = pygame.sndarray.array(base_sound)
            orig_len = len(raw_array)

            variants_for_this_sound = []
            factors = np.linspace(pitch_range[0], pitch_range[1], pitch_variations)

            for factor in factors:
                indices = np.round(np.arange(0, orig_len, factor)).astype(int)
                indices = indices[indices < orig_len]
                shifted_array = raw_array[indices]

                variant = pygame.sndarray.make_sound(shifted_array)
                variant.set_volume(volume)
                variants_for_this_sound.append(variant)

            self.sound_variants.append(variants_for_this_sound)

    def play(self, volume=None, play=True):
        """Farklı bir temel sesi rastgele seçer ve onun rastgele perdesini çalar."""
        if not self.sound_variants:
            return

        # Tekrar engelleme: 2 veya daha fazla ses varsa aynı ses üst üste çalmasın
        if len(self.sound_variants) > 1:
            available_indices = [i for i in range(len(self.sound_variants)) if i != self.last_played_idx]
            chosen_idx = random.choice(available_indices)
        else:
            chosen_idx = 0

        self.last_played_idx = chosen_idx

        # Seçilen sesin önbelleğe alınmış rastgele bir perdesini çal
        chosen_variant = random.choice(self.sound_variants[chosen_idx])

        if play:
            if volume:
                chosen_variant.set_volume(volume)
            chosen_variant.play()

class SoundFX:
    def __init__(self, filepath, volume=1.0, pitch_variations=7, pitch_range=(0.92, 1.08)):
        """
        Pitch Randomization destekli ses nesnesi.
        - filepath: .wav veya .ogg ses dosyasının yolu
        - pitch_range: (min, max) frekans çarpanı (Örn: 0.92 = tok, 1.08 = tiz)
        - pitch_variations: Oyun başlamadan kaç farklı perde üretilip önbelleğe alınacağı
        """
        self.base_sound = pygame.mixer.Sound(filepath)
        self.base_sound.set_volume(volume)
        self.variations = []

        # Ham ses verisini NumPy dizisine çevir
        raw_array = pygame.sndarray.array(self.base_sound)
        orig_len = len(raw_array)

        # Farklı frekans çarpanlarında önbellek sesleri üret
        factors = np.linspace(pitch_range[0], pitch_range[1], pitch_variations)
        
        for factor in factors:
            # Sesi yeniden örnekle (resampling mantığı ile perde değiştirme)
            indices = np.round(np.arange(0, orig_len, factor)).astype(int)
            indices = indices[indices < orig_len]
            shifted_array = raw_array[indices]

            sound_variant = pygame.sndarray.make_sound(shifted_array)
            sound_variant.set_volume(volume)
            self.variations.append(sound_variant)

    def play(self):
        """Önbellekteki perde varyasyonlarından rastgele birini anında çalar."""
        if self.variations:
            random.choice(self.variations).play()
        else:
            self.base_sound.play()

    def set_volume(self, volume: float):
        """SFX'in sesini değiştirir."""

        if self.variations:
            for var in self.variations:
                var.set_volume(volume)

        else:
            self.base_sound.set_volume(volume)
