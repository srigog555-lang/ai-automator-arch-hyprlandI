# AI Automator — Arch + Hyprland Minimal Initial Implementation

This repository contains a conservative, secure scaffolding for an "AI Automator" that integrates with Hyprland
on Arch Linux. The goal of the project is to provide a local, optionally connected, automation assistant specialized
for Hyprland environments.

This initial commit contains a skeleton: idempotent installer, Python daemon skeleton, Hyprland parser, DB wrapper,
web dashboard, and a gated action dispatcher. It intentionally requires user opt-in to enable dangerous actions.

## Security & safety notes
 - This tool is powerful. You must opt-in to enable remote actions by toggling `enable_dispatch` in `~/.config/ai-automator/config.yaml`.
- The Gemini API key (if provided) is encrypted with a local symmetric key stored at `~/.local/share/ai-automator/secret.key`.
- All local data is stored in `~/.local/share/ai-automator` and `~/.config/ai-automator`. Do not share those files.

## Getting started
1. Ensure you are on Arch Linux with Hyprland. Install `git` and `python`.
2. Clone this repository or unzip the GitHub release.
3. Run the installer from the repo dir:

```bash
./install.sh
```

The installer will:
- check for necessary packages and optionally install them using pacman or your AUR helper
- generate a local Fernet key to encrypt the Gemini API key
- set up a systemd user service at `~/.config/systemd/user/ai-automator.service`
- create a python virtualenv and install python dependencies

4. After install, open the dashboard: http://127.0.0.1:8080

## Installation: step-by-step
Follow these steps to install and run `ai-automator` on Arch Linux in a Hyprland session. These steps are intentionally explicit to emphasize audit, user consent, and gating for powerful actions.

1) Clone the repo (or unzip the release):

```bash
git clone https://github.com/<your-username>/ai-automator-arch-hyprlandI.git
cd ai-automator-arch-hyprlandI
```

2) Run the installer from the repository root (it will prompt to install missing dependencies):

```bash
./install.sh
```

The script will:
- check for packages and install missing ones with pacman (optional by prompt)
- offer to install `ydotool` from AUR via an AUR helper like `paru` or `yay`, or build it with the included `scripts/build_ydotool.sh`
- set up a Python virtualenv at `~/.local/share/ai-automator/venv` and install the pip requirements
- copy repository files to `~/.local/share/ai-automator` and create a wrapper CLI `~/.local/bin/ai-automator`
- generate `~/.local/share/ai-automator/secret.key` and optionally store your Gemini API key encrypted at `~/.config/ai-automator/config.ini`
- create and attempt to start a user-level systemd service `~/.config/systemd/user/ai-automator.service`

3) Check the service status (if you enabled systemd start during install):

```bash
systemctl --user status ai-automator
journalctl --user -u ai-automator -f
```

4) Open the local dashboard at `http://127.0.0.1:8080` in your browser to see the event feed and connect the WebSocket chat.

5) Use the safe CLI to review missing tools and toggle physical-action dispatch:

```bash
python -m ai_automator.safe_cli audit
python -m ai_automator.safe_cli enable  # (enables `enable_dispatch` in ~/.config/ai-automator/config.yaml — be careful)
python -m ai_automator.safe_cli disable
```

6) To securely add your Gemini API key anytime after install:

```bash
python -m ai_automator.cli configure
```

## How it works (overview)
The system is designed to be safe, auditable, and privacy-first while providing strong automation:

- Audit & discovery: on install and periodically, the daemon scans for key tools (e.g., `grim`, `slurp`, `hyprctl`, `ydotool`), parses `~/.config/hypr/hyprland.conf` for binds, and indexes common dotfiles (neovim, waybar, wofi, mpd). The data is recorded to the local SQLite DB at `~/.local/share/ai-automator/context_db.sqlite`.

- Local memory & encryption: sensitive items (the Gemini key) are encrypted with a local `secret.key` and only accessible to the user-level daemon. All other indexed facts are stored in plaintext SQLite but never transmitted remotely without explicit consent.

- Daemon & events: `ai_automator/daemon.py` runs as a user `systemd` service. It polls `hyprctl` for active window and monitors by default (future versions will read the Hyprland event socket if available) and writes events to the local DB.

- WebSocket & dashboard: a lightweight `aiohttp` server provides a WebSocket endpoint for the dashboard at `127.0.0.1:8080/ws`. The UI shows live events and allows local chat input.

- Action dispatcher: sensitive actions (synthesizing input with `ydotool`, `hyprctl` dispatch, `pactl` volume control, `playerctl`, running commands) are gated behind `enable_dispatch` in `~/.config/ai-automator/config.yaml`. The `safe_cli` lets the user toggle this and the dashboard will show confirmation prompts before actions are executed.

- Context & LLM: when you ask a question that benefits from AI reasoning, the daemon can build a context window that includes the relevant local state (active window, workspace, keybindings, recent commands, an encoded screenshot if the user authorizes it) and send it to Gemini or a local LLM — but only if you provide an API key and explicitly enable network access.

## Example flows & CLI commands
- Start a coding session (example macro — `enable_dispatch` required):

```bash
# toggle dispatch at your own risk
python -m ai_automator.safe_cli enable

# then the admin will confirm the macro before executing from the dashboard
```

- Check the audit results and missing dependencies (dry run):

```bash
python -m ai_automator.cli audit
```

- Configure the Gemini API key in the future (safely encrypted locally):

```bash
python -m ai_automator.cli configure
```

## Packaging & final distribution
- To create a single ZIP you can upload to GitHub (e.g., for a release):

```bash
zip -r ai-automator-arch-hyprland.zip . -x '*.git/*' -x '*.pytest_cache/*' -x '*/__pycache__/*'
```

Be sure to review `install.sh` and `systemd/ai-automator.service` for security and distribution policies before uploading.

## File organization
- `install.sh`: idempotent installer script for Arch
- `ai_automator/daemon.py`: main async daemon skeleton for events and websocket
- `ai_automator/audit.py`: system dependency checks and read-only discovery
- `ai_automator/hypr_parser.py`: safe hyprland parser for keybinds
- `ai_automator/db.py`: encrypted key + sqlite helper
- `ai_automator/dispatcher.py`: action dispatcher (gated behind `enable_dispatch`)
- `frontend/static/index.html`: simple websocket chat for now

## Limitations & future work
- The current hyprctl integration polls for activewindow/monitors every 5s; implement socket listener for Hyprland events.
- Add safe sandbox for running shell commands with fine-grained permissions.
- Implement robust log viewer and chat components, with local LLM fallback.
- Implement ydotool build step within install script if user opts in.

## Contributing & License
- This repository is a scaffold: contributions should focus on security/permissions and strong unit tests.
# ai-automator-arch-hyprlandI
