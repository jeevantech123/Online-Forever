import asyncio
import json
import requests
import websockets
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

    def log_message(self, format, *args):
        pass  # suppress noisy request logs

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

TOKEN = os.environ.get("TOKEN")
STATUS = "idle"  # online / dnd / idle
CUSTOM_STATUS = "Starlight over the seas!"  # Leave empty if you don't want a custom status
USE_EMOJI = True
print(repr(TOKEN))
headers = {"Authorization": TOKEN}

r = requests.get("https://discord.com/api/v10/users/@me", headers=headers)
if r.status_code != 200:
    print("Invalid token!")
    exit()

user = r.json()
print(f"Logged in as {user['username']} ({user['id']})!")

activity = {
    "name": "Custom Status",
    "type": 4,
    "state": CUSTOM_STATUS,
    "id": "custom"
}

if USE_EMOJI:
    activity["emoji"] = {
        "name": "✨",   # Unicode emoji or emoji name
        "id": None,     # Required only for custom emojis
        "animated": False
    }

async def discord_gateway():
    uri = "wss://gateway.discord.gg/?v=10&encoding=json"

    async with websockets.connect(uri) as ws:
        hello = json.loads(await ws.recv())
        heartbeat_interval = hello["d"]["heartbeat_interval"]

        async def heartbeat():
            while True:
                await asyncio.sleep(heartbeat_interval / 1000)
                await ws.send(json.dumps({"op": 1, "d": None}))

        asyncio.create_task(heartbeat())

        identify = {
            "op": 2,
            "d": {
                "token": TOKEN,
                "properties": {
                    "$os": "windows",
                    "$browser": "chrome",
                    "$device": "pc"
                },
                "presence": {
                    "status": STATUS,
                    "afk": False,
                    "activities": [activity]
                }
            }
        }
        await ws.send(json.dumps(identify))

        while True:
            try:
                msg = await ws.recv()
                data = json.loads(msg)

                if data.get("op") == 11:
                    pass

            except Exception as e:
                print("Connection lost, reconnecting...", e)
                break
        await asyncio.sleep(5)

while True:
    asyncio.run(discord_gateway())
