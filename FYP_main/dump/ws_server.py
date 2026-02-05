import asyncio
import json
import websockets

CLIENTS = set()

async def handler(websocket):
    CLIENTS.add(websocket)
    print("[WS] Client connected")

    try:
        async for message in websocket:
            data = json.loads(message)
            for client in CLIENTS:
                if client.open:
                    await client.send(json.dumps(data))
    except websockets.exceptions.ConnectionClosed:
        print("[WS] Client disconnected")
    finally:
        CLIENTS.remove(websocket)

async def main():
    print("[WS] Running at ws://localhost:9001")
    async with websockets.serve(handler, "localhost", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())