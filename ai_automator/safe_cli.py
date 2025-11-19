#!/usr/bin/env python3
"""Provide small helper commands for auditing and toggling dispatch (safe by CLI, requires user confirmation).
"""
import argparse
from ai_automator import audit, db
from pathlib import Path
import yaml

CONFIG = Path.home() / '.config' / 'ai-automator' / 'config.yaml'


def _load_cfg():
    if not CONFIG.exists():
        CONFIG.parent.mkdir(parents=True, exist_ok=True)
        CONFIG.write_text('enable_dispatch: false\n')
    return yaml.safe_load(CONFIG.read_text()) or {}


def _save_cfg(d):
    CONFIG.write_text(yaml.safe_dump(d))


def toggle_dispatch(enable):
    d = _load_cfg()
    d['enable_dispatch'] = bool(enable)
    _save_cfg(d)
    print('enable_dispatch =', d['enable_dispatch'])


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('cmd', choices=['audit','enable','disable'])
    args = p.parse_args()
    if args.cmd == 'audit':
        print('Missing tools:', audit.check_dependencies())
    elif args.cmd == 'enable':
        toggle_dispatch(True)
    else:
        toggle_dispatch(False)
