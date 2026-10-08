# syntax=docker/dockerfile:1
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# 1. APT Önbelleği: Ubuntu'nun otomatik paket silme kuralını kaldırıyoruz
# ve apt listeleri ile .deb arşivlerini BuildKit cache mount'a bağlıyoruz.
RUN rm -f /etc/apt/apt.conf.d/docker-clean && \
    echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libfontconfig1 \
    libfreetype6

WORKDIR /game

# 2. PIP Önbelleği: requirements.txt değişse bile daha önce indirilmiş
# kütüphaneler /root/.cache/pip üzerinden anında yüklenir.
COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
    python3 -m pip install --upgrade pip && \
    pip3 install -r requirements.txt

# 3. Kod Dosyaları (.dockerignore sayesinde build/dist içeri kopyalanmaz)
COPY . .

# 4. PyInstaller Derlemesi
# PyInstaller'ın kendi disk önbelleğini de (/root/.cache/pyinstaller) bağlayabilirsiniz.
RUN --mount=type=cache,target=/root/.cache/pyinstaller \
    pyinstaller \
    --clean \
    --noconfirm \
    main2.spec

# --- YENİ ADIM: BuildKit İhracat Katmanı ---
FROM scratch AS export
COPY --from=0 /game/dist/main2 /