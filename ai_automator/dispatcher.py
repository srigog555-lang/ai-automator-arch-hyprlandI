"""Action dispatcher — converts JSON action plan into local actions.

This is designed to be very explicit and to require user opt-in. Any action request
that is sensitive (keyboard/mouse/commands) requires that `enable_dispatch` be true
in `~/.config/ai-automator/config.yaml`.

This skeleton includes safe scaffolding for actions like hyprctl dispatch, playerctl,
volume control, and file editing. It does not tin-foil wrap arbitrary shell execution
unless explicitly allowed by the user.
"""

import subprocess
from pathlib import Path
import yaml

CONFIG = Path.home() / '.config' / 'ai-automator' / 'config.yaml'


def _load_cfg():
    if not CONFIG.exists():
        return {}
    return yaml.safe_load(open(CONFIG)) or {}


def _enabled():
    cfg = _load_cfg()
    return cfg.get('enable_dispatch', False)


def run_command(cmd, allow_shell=False):
    if not _enabled():
        raise PermissionError('Dispatcher disabled; enable `enable_dispatch` in config.yaml to allow action')
    # disallow dangerous shell expansion by default
    if allow_shell:
        return subprocess.run(cmd, shell=True, check=False)
    else:
        return subprocess.run(cmd, check=False)


def hypr_dispatch(action):
    """Run a hyprctl dispatcher command, such as 'exec,"emacs"' or 'dispatch layout togglefloating'.
    action is a string; ensure it's not overly broad.
    """
    if not _enabled():
        raise PermissionError('Dispatcher disabled')
    # Example: action = 'dispatch workspace 3'
    return subprocess.run(["hyprctl", *action.split()], check=False)


def synthesize_input(keys):
    """Synthesize keyboard input using ydotool if available. keys should be a list of key strings.
    ydotool must be installed and the user must enable dispatch.
    """
    if not _enabled():
        raise PermissionError('Dispatcher disabled')
    if Path('/usr/bin/ydotool').exists() or Path('/usr/local/bin/ydotool').exists():
        # naive implementation for simple keys
        for k in keys:
            subprocess.run(['ydotool', 'key', k], check=False)
    else:
        raise FileNotFoundError('ydotool not found; cannot synthesize input')
