import asyncio
import json
import websockets

WS_URL = "ws://localhost:9001"

def send_event(event_type, payload):
    async def _send():
        async with websockets.connect(WS_URL) as ws:
            await ws.send(json.dumps({
                "event": event_type,
                "data": payload
            }))

    try:
        asyncio.run(_send())
    except RuntimeError:
        loop = asyncio.get_event_loop()
        loop.create_task(_send())