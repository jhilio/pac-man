#!/usr/bin/env bash
set -e

export WINEPREFIX="$HOME/.wine-pacman"
export KMP_AFFINITY=disabled
export KMP_HW_SUBSET=1T
export OMP_NUM_THREADS=1

rm -rf build dist

echo "==> Building Linux version..."

uv run pyinstaller \
  --onedir \
  --strip \
  --upx-dir /usr/bin \
  --add-data "assets:assets" \
  --add-data "models:models" \
  --add-data "config.json:." \
  --name pac-man-linux \
  pac-man.py

echo "==> Building Windows version..."

wine python -m PyInstaller \
  --onedir \
  --add-data "assets;assets" \
  --add-data "models;models" \
  --add-data "config.json;." \
  --name pac-man-windows \
  pac-man.py

echo
echo "==> Builds complete:"

zip -r dist/linux.zip dist/pac-man-linux
zip -r dist/windows.zip dist/pac-man-windows

ls -lh dist
