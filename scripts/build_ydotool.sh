#!/usr/bin/env bash
# Build ydotool from AUR if AUR helper isn't available.
set -euo pipefail

if command -v paru >/dev/null 2>&1; then
  paru -S --noconfirm ydotool
elif command -v yay >/dev/null 2>&1; then
  yay -S --noconfirm ydotool
else
  echo "No AUR helper found. Building manually from AUR..."
  tmpdir=$(mktemp -d)
  pushd "$tmpdir"
  git clone https://aur.archlinux.org/ydotool.git
  cd ydotool
  makepkg -si --noconfirm
  popd
  rm -rf "$tmpdir"
fi
