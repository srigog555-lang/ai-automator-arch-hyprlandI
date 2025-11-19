"""Simple sqlite DB wrapper with an encrypted key for storing the Gemini API key.
"""
from pathlib import Path
import aiosqlite
from cryptography.fernet import Fernet
import os

DATA_DIR = Path.home() / '.local' / 'share' / 'ai-automator'
CONFIG_DIR = Path.home() / '.config' / 'ai-automator'
DB_PATH = DATA_DIR / 'context_db.sqlite'
SECRET_KEY = DATA_DIR / 'secret.key'
CONFIG_FILE = CONFIG_DIR / 'config.ini'


class DB:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    async def init(self):
        self.conn = await aiosqlite.connect(DB_PATH)
        await self.conn.execute('CREATE TABLE IF NOT EXISTS memory(k TEXT PRIMARY KEY, v BLOB)')
        await self.conn.execute('CREATE TABLE IF NOT EXISTS history(k TEXT, v TEXT, ts DATETIME DEFAULT CURRENT_TIMESTAMP)')
        await self.conn.commit()

    async def close(self):
        await self.conn.close()

    async def set(self, key, value):
        await self.conn.execute('INSERT OR REPLACE INTO memory(k, v) VALUES (?,?)', (key, value))
        await self.conn.commit()

    async def get(self, key):
        async with self.conn.execute('SELECT v FROM memory WHERE k=?', (key,)) as cur:
            row = await cur.fetchone()
            if row: return row[0]
            return None


# config encryption + helpers

def load_secret_key():
    if not SECRET_KEY.exists():
        return None
    return open(SECRET_KEY, 'rb').read()


def store_encrypted_gemini(api_key: str):
    key = load_secret_key()
    if not key:
        raise RuntimeError('No secret generated — run install.sh again')
    f = Fernet(key)
    enc = f.encrypt(api_key.encode())
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    open(CONFIG_FILE, 'wb').write(enc)


def load_gemini_key():
    key = load_secret_key()
    if not key:
        return None
    if not CONFIG_FILE.exists():
        return None
    f = Fernet(key)
    try:
        return f.decrypt(open(CONFIG_FILE,'rb').read()).decode()
    except Exception:
        return None
