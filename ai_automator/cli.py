#!/usr/bin/env python3
import argparse
from ai_automator import db
import getpass


def configure():
    print('Enter Gemini API key (blank to skip):')
    key = getpass.getpass()
    if key:
        db.store_encrypted_gemini(key)
        print('Gemini API key stored.')
    else:
        print('Skipped.')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('command', choices=['configure','audit'])
    args = p.parse_args()
    if args.command == 'configure':
        configure()
    else:
        from ai_automator import audit
        missing = audit.check_dependencies()
        print('Missing tools: ', missing)
