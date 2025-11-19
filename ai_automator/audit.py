"""Audit helpers to detect installed packages, check for required tools and create a discovery fingerprint.
"""
import shutil
import subprocess
import logging
from pathlib import Path
import os

LOG = logging.getLogger("ai_automator.audit")

REQUIRED = ["python3", "jq", "grim", "slurp", "hyprctl"]
AUR_OPTIONAL = ["ydotool"]

def which(cmd):
    path = shutil.which(cmd)
    LOG.debug("which(%s) -> %s", cmd, path)
    return path

def check_dependencies():
    missing = []
    for c in REQUIRED:
        if not which(c): missing.append(c)
    return missing


def get_hyprland_config():
    home = Path.home()
    locations = [home / ".config" / "hypr" / "hyprland.conf", home / ".config" / "hyprland.conf"]
    for p in locations:
        if p.exists():
            return p
    return None


def read_hypr_config():
    config = get_hyprland_config()
    if not config:
        LOG.info("No hyprland config found")
        return ""
    return config.read_text()


def signature():
    # simple fingerprint for a system
    res = {
        'python3': which('python3') is not None,
        'grit': which('grim') is not None,
        'wl-copy': which('wl-copy') is not None,
    }
    try:
        res['uname'] = subprocess.check_output(['uname', '-a']).decode().strip()
    except Exception:
        res['uname'] = None
    return res
