#!/usr/bin/env bash
# install.sh — idempotent installer for ai-automator on Arch Linux (Hyprland-focused)
# This script checks for required dependencies, optionally installs them via pacman/AUR helper,
# creates a Python virtualenv, installs Python dependencies, sets up config dir and systemd user service,
# and initializes an encrypted local database/secret key for local memory and Gemini API storage.

set -euo pipefail
IFS=$'\n\t'

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$HOME/.local/share/ai-automator"
CONFIG_DIR="$HOME/.config/ai-automator"
BIN_DIR="$HOME/.local/bin"
SERVICE_FILE="$HOME/.config/systemd/user/ai-automator.service"
VENV_DIR="$DATA_DIR/venv"
PYTHON=$(which python3 || true)

die(){ echo "ERROR: $*" >&2; exit 1; }
info(){ echo "[INFO] $*"; }
confirm(){ read -r -p "$1 [y/N]: " resp; case "$resp" in [yY]|[yY][eE][sS]) return 0;; *) return 1;; esac }

# Ensure directories
mkdir -p "$DATA_DIR" "$CONFIG_DIR" "$BIN_DIR"

# Check for pacman
if ! command -v pacman >/dev/null 2>&1; then
  die "This installer is for Arch Linux. pacman not found." 
fi

# Detect AUR helper preference
AUR_HELPER=""
for h in paru yay; do
  if command -v "$h" >/dev/null 2>&1; then
    AUR_HELPER="$h"; break
  fi
done

# Dependency lists
PACMAN_PKGS=(python python-pip jq curl git grim slurp wayland-utils llvm libxkbcommon dbus libcap elogind wireplumber wl-clipboard)
AUR_PKGS=(ydotool)

# Check function
check_install(){ local cmd="$1"; if command -v "$cmd" >/dev/null 2>&1; then echo "ok"; else echo "missing"; fi }

info "Performing initial dependency audit..."
MISSING=()
for pkg in python python3 git jq curl grim slurp; do
  if ! command -v "$pkg" >/dev/null 2>&1; then MISSING+=("$pkg"); fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
  echo "The following packages are missing: ${MISSING[*]}"
  if confirm "Install missing packages using pacman?"; then
    sudo pacman -Syu --needed --noconfirm "${MISSING[@]}"
  else
    info "Skipping package installation. You must install these before continuing: ${MISSING[*]}"
  fi
fi

# AUR package ydotool
if ! command -v ydotool >/dev/null 2>&1; then
  if [ -n "$AUR_HELPER" ]; then
    if confirm "ydotool not found. Install ydotool from AUR using $AUR_HELPER?"; then
      $AUR_HELPER -S --noconfirm ydotool || echo "Failed to install ydotool automatically. You can build it from AUR()"
    fi
  else
    echo "ydotool not found and no AUR helper found. Please install ydotool from the AUR manually for input synthesis."
  fi
fi

# Create python venv
if [ ! -d "$VENV_DIR" ]; then
  info "Creating python venv in $VENV_DIR"
  python3 -m venv "$VENV_DIR"
fi

# Activate venv and install pip deps
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"
if [ -f "$REPO_DIR/requirements.txt" ]; then
  pip install --upgrade pip
  pip install -r "$REPO_DIR/requirements.txt"
else
  pip install --upgrade pip
  pip install fastapi uvicorn websockets aiohttp aiosqlite cryptography pyyaml
fi

# Make the ai_automator package importable inside the venv by installing editable
cd "$REPO_DIR"
pip install --upgrade pip
pip install -e .
cd - >/dev/null

# Create systemd user service
cat > "$SERVICE_FILE" <<'EOF'
[Unit]
Description=AI Automator for Hyprland — user daemon
After=graphical-session.target

[Service]
Type=simple
Environment=PYTHONUNBUFFERED=1
ExecStart=%h/.local/share/ai-automator/venv/bin/python %h/.local/share/ai-automator/ai_automator/daemon.py
Restart=always
RestartSec=3

[Install]
WantedBy=default.target
EOF

# Create python script wrapper in local bin
cat > "$BIN_DIR/ai-automator" <<'EOF'
#!/usr/bin/env bash
source "$HOME/.local/share/ai-automator/venv/bin/activate"
python "$HOME/.local/share/ai-automator/ai_automator/daemon.py" "$@"
EOF
chmod +x "$BIN_DIR/ai-automator"

# Copy repository files into data dir (idempotent)
rsync -a --delete "$REPO_DIR/" "$DATA_DIR/"

# Initialize secrets: generate Fernet key and store in $DATA_DIR/secret.key
if [ ! -f "$DATA_DIR/secret.key" ]; then
  info "Generating local encryption key to protect API credentials..."
  python - <<'PY'
from cryptography.fernet import Fernet
import os
DATA_DIR = os.path.expanduser('~/.local/share/ai-automator')
key = Fernet.generate_key()
open(os.path.join(DATA_DIR, 'secret.key'), 'wb').write(key)
PY
  chmod 600 "$DATA_DIR/secret.key"
fi

# Ask for Gemini API key and store encrypted
if [ ! -f "$CONFIG_DIR/config.ini" ]; then
  echo "Please enter your Gemini API key (leave blank to skip / run offline):"
  read -r GEMINI_KEY
  if [ -n "${GEMINI_KEY}" ]; then
    python - <<'PY'
from cryptography.fernet import Fernet
import os
DATA_DIR = os.path.expanduser('~/.local/share/ai-automator')
CONFIG_DIR = os.path.expanduser('~/.config/ai-automator')
key = open(os.path.join(DATA_DIR, 'secret.key'),'rb').read()
F = Fernet(key)
enc = F.encrypt(b"%s")
open(os.path.join(CONFIG_DIR, 'config.ini'),'wb').write(enc)
PY
    chmod 600 "$CONFIG_DIR/config.ini"
    info "Gemini API key securely stored in $CONFIG_DIR/config.ini"
  else
    info "Skipping Gemini API key storage — you can add one later with ai-automator configure"
  fi
fi

# Enable and start systemd user service
systemctl --user daemon-reload
systemctl --user enable --now ai-automator.service || true

# Print final info
info "Install finished. Use 'systemctl --user status ai-automator' to check the service."
info "Run 'ai-automator --help' to see usage (provided once daemon implements CLI)."

echo "DONE"
