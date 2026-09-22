FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
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
    libfreetype6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /game

COPY requirements.txt .

RUN python3 -m pip install --upgrade pip && \
    pip3 install -r requirements.txt

COPY . .

# Kontrol amaçlı
RUN echo "=== /game içeriği ===" && \
    pwd && \
    ls -la && \
    echo "=== Python dosyaları ===" && \
    ls -la *.py

RUN rm -rf build dist

RUN pyinstaller \
    --clean \
    --noconfirm \
    main2.spec