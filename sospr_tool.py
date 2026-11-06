import struct
import json
import io
import pygame

MAGIC = b"SO1S"
FORMAT_VERSION = 2

def pack_spritesheet(
    image_path: str,
    output_path: str,
    rows: int,
    cols: int,
    row_names: list[str],
    frame_counts: list[int] | None = None
):
    """
    Spritesheet görselini ve satır başı kare sayılarını .sospr ikili formatına paketler.
    
    :param frame_counts: Her satırda kaç geçerli kare olduğu (örn: [4, 6, 3, 2]). 
                         None verilirse tüm satırlar `cols` kadar kare içerir.
    """
    if len(row_names) != rows:
        raise ValueError(f"Satır sayısı ({rows}) ile row_names boyutu ({len(row_names)}) uyuşmuyor.")

    if frame_counts is None:
        frame_counts = [cols] * rows
    elif len(frame_counts) != rows:
        raise ValueError(f"Satır sayısı ({rows}) ile frame_counts boyutu ({len(frame_counts)}) uyuşmuyor.")

    for count in frame_counts:
        if count < 1 or count > cols:
            raise ValueError(f"Kare sayısı 1 ile {cols} arasında olmalıdır. Hatalı değer: {count}")

    # Görsel verisini oku ve boyutları hesapla
    with open(image_path, "rb") as f:
        img_bytes = f.read()

    temp_surf = pygame.image.load(io.BytesIO(img_bytes))
    total_w, total_h = temp_surf.get_size()

    frame_w = total_w // cols
    frame_h = total_h // rows

    # Metaveri sözlüğü
    animations_meta = [
        {"name": name, "count": count}
        for name, count in zip(row_names, frame_counts)
    ]

    metadata = {
        "rows": rows,
        "cols": cols,
        "frame_width": frame_w,
        "frame_height": frame_h,
        "animations": animations_meta
    }

    meta_bytes = json.dumps(metadata, ensure_ascii=False).encode("utf-8")

    # İkili paketi diske yazma
    with open(output_path, "wb") as f:
        # Header (4 bayt Magic + 2 bayt Sürüm)
        f.write(MAGIC)
        f.write(struct.pack(">H", FORMAT_VERSION))

        # Metaveri Bölümü
        f.write(struct.pack(">I", len(meta_bytes)))
        f.write(meta_bytes)

        # Görsel Verisi Bölümü
        f.write(struct.pack(">I", len(img_bytes)))
        f.write(img_bytes)

    print(f"Paketleme başarılı -> {output_path}")


def load_sospr(file_path: str) -> dict[str, list[pygame.Surface]]:
    """
    .sospr dosyasını okur. Boş kareleri atlayarak sadece belirtilen kare sayısı
    kadar pygame.Surface üretir.
    """
    with open(file_path, "rb") as f:
        magic = f.read(4)
        if magic != MAGIC:
            raise ValueError("Geçersiz dosya: Magic header eşleşmiyor.")

        version, = struct.unpack(">H", f.read(2))

        meta_len, = struct.unpack(">I", f.read(4))
        meta_bytes = f.read(meta_len)
        metadata = json.loads(meta_bytes.decode("utf-8"))

        img_len, = struct.unpack(">I", f.read(4))
        img_bytes = f.read(img_len)

    # Pygame yüzeyini yükle
    sheet_surface = pygame.image.load(io.BytesIO(img_bytes)).convert_alpha()

    frame_w = metadata["frame_width"]
    frame_h = metadata["frame_height"]
    animations = {}

    for row_idx, anim_data in enumerate(metadata["animations"]):
        name = anim_data["name"]
        count = anim_data["count"]
        frames = []

        # Yalnızca geçerli kare sayısı kadar kesim yap
        for col_idx in range(count):
            rect = pygame.Rect(col_idx * frame_w, row_idx * frame_h, frame_w, frame_h)
            frame_surf = sheet_surface.subsurface(rect).copy()
            frames.append(frame_surf)

        animations[name] = frames

    return animations
