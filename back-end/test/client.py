from websockets.sync.client import connect
import asyncio
import time

async def hello():
    with connect("ws://localhost:8080") as websocket:
        for i in range(10):
            websocket.send("Hello world!")
            time.sleep(0.5)
    websocket.close()

asyncio.run(hello())