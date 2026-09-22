#!/bin/bash

set -e

IMAGE_NAME="savas-oyunu-build"
CONTAINER_NAME="savas-oyunu-build-container"

echo "======================================"
echo " Savaş Oyunu 1 - Linux Build"
echo " Ubuntu 22.04 / glibc 2.35 hedefi"
echo "======================================"

echo
echo "[1/3] Docker image oluşturuluyor..."
docker build --no-cache --tag "$IMAGE_NAME" .

echo
echo "[2/3] Container oluşturuluyor..."

docker rm "$CONTAINER_NAME" 2>/dev/null || true

docker create \
    --name "$CONTAINER_NAME" \
    "$IMAGE_NAME"

echo
echo "[3/3] dist/main2 dışarı aktarılıyor..."

rm -rf dist

docker cp \
    "$CONTAINER_NAME:/game/dist/main2" \
    "./dist"

docker rm "$CONTAINER_NAME"

echo
echo "======================================"
echo " BUILD TAMAMLANDI!"
echo "======================================"
echo
echo "Çıktı:"
echo "dist/main2/"
echo
echo "Çalıştırmak için:"
echo "./dist/main2/savas_oyunu1"