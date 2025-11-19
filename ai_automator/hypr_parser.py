"""Small Hyprland configuration parser — extracts bind lines and monitor layout info using hyprctl.
This parser intentionally only performs safe reads of text config and the hyprctl -j output; it does NOT execute
any code from the user's dotfiles.
"""

from pathlib import Path
import re
import json

BIND_RE = re.compile(r"^(bind|bindcode)\s*=\s*(.+)\s+(\S.*)$")


def parse_keybinds(conf_text: str):
    binds = []
    for ln in conf_text.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith('#'):
            continue
        m = BIND_RE.match(ln)
        if m:
            typ = m.group(1)
            combo = m.group(2).strip()
            action = m.group(3).strip()
            binds.append({'type': typ, 'combo': combo, 'action': action})
    return binds


def get_local_config():
    home = Path.home()
    candidates = [home / '.config' / 'hypr' / 'hyprland.conf', home / '.config' / 'hyprland.conf']
    for p in candidates:
        if p.exists():
            return p
    return None


def parse_local():
    p = get_local_config()
    if not p:
        return []
    text = p.read_text()
    return parse_keybinds(text)


def hyprctl_monitors_json():
    import subprocess
    try:
        out = subprocess.check_output(['hyprctl', 'monitors', '-j'])
        return json.loads(out)
    except Exception:
        return None
