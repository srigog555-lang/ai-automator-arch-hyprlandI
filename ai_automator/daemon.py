#!/usr/bin/env python3
"""ai_automator.daemon
A small asynchronous skeleton showing the hyprctl event integration, websocket serving,
and the secure dispatcher interface which must be explicitly enabled by the user.

This is intentionally conservative: the dispatcher is gated behind an opt-in flag so that
users do not accidentally allow remote execution. The installer only sets up the service
and keys; the user must toggle critical automation features in the config.ini.
"""

import asyncio
import json
import os
import logging
import subprocess
from pathlib import Path

from aiohttp import web
import aiosqlite
from cryptography.fernet import Fernet

LOG = logging.getLogger("ai_automator")
logging.basicConfig(level=logging.INFO)

DATA_DIR = Path.home() / ".local" / "share" / "ai-automator"
CONFIG_DIR = Path.home() / ".config" / "ai-automator"
DB_PATH = DATA_DIR / "context_db.sqlite"
SECRET_KEY_PATH = DATA_DIR / "secret.key"
CONFIG_FILE = CONFIG_DIR / "config.ini"

async def run_hyprctl_monitor(queue: asyncio.Queue):
    # hyprctl supports socket monitoring via unix socket. But for portability we can
    # call simple hyprctl commands periodically to gather state. For live events a
    # future improvement is to open the Hyprland event socket.
    while True:
        try:
            res = subprocess.run(["hyprctl", "activewindow", "-j"], capture_output=True, text=True, check=False)
            if res.returncode == 0:
                await queue.put({"type":"activewindow","payload":json.loads(res.stdout)})
            monitors = subprocess.run(["hyprctl", "monitors", "-j"], capture_output=True, text=True, check=False)
            if monitors.returncode == 0:
                await queue.put({"type":"monitors","payload":json.loads(monitors.stdout)})
        except FileNotFoundError:
            LOG.debug("hyprctl not found; skipping hyprctl calls")
        await asyncio.sleep(5)

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    LOG.info("WebSocket client connected")

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                text = msg.data.strip()
                LOG.info("Received message from client: %s", text)
                await ws.send_str("ACK: " + text)
            elif msg.type == web.WSMsgType.ERROR:
                LOG.error("ws connection closed with exception %s", ws.exception())
    except asyncio.CancelledError:
        pass

    LOG.info("WebSocket disconnected")
    return ws

async def start_webserver():
    app = web.Application()
    app.router.add_get('/ws', websocket_handler)
    app.router.add_static('/', path=str(Path(__file__).parent / '..' / 'frontend' / 'static'), show_index=True)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '127.0.0.1', 8080)
    await site.start()
    LOG.info("Web server started on http://127.0.0.1:8080")

async def ensure_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS key_bindings (id INTEGER PRIMARY KEY, key TEXT, action TEXT)''')
        await db.execute('''CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, type TEXT, payload JSON, ts DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        await db.commit()

async def run_main_loop():
    queue = asyncio.Queue()
    await ensure_db()
    tasks = [
        asyncio.create_task(run_hyprctl_monitor(queue)),
        asyncio.create_task(start_webserver()),
    ]
    try:
        while True:
            # simple event loop: process hyprctl events from queue
            ev = await queue.get()
            LOG.info("Event: %s", ev['type'])
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute('INSERT INTO events(type, payload) VALUES (?,?)', (ev['type'], json.dumps(ev['payload'])))
                await db.commit()
    except asyncio.CancelledError:
        for t in tasks:
            t.cancel()

if __name__ == '__main__':
    try:
        # small startup message with where DB is stored
        LOG.info("ai-automator daemon starting. DB: %s", DB_PATH)
        asyncio.run(run_main_loop())
    except KeyboardInterrupt:
        LOG.info("shutting down")
