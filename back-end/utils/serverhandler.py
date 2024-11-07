import websockets
import asyncio
import threading

from websockets.legacy.server import WebSocketServerProtocol

class WebsocketServer:
    # This set holds all of the active "clients" (WebSocket connections) that are communicating with the server.
    active_clients = set()

    # This method is called when a websocket is connected to the server.
    async def handle_websocket(self, websocket: WebSocketServerProtocol, path):
        self.active_clients.add(websocket)
        try:
            while True:
                async for message in websocket:
                    for client in self.active_clients:
                        await client.send(message)
                        print(message)
        except websockets.ConnectionClosed:
            self.active_clients.remove(websocket)
        
    # Creates a new loop to handle_websocket method to process new incoming connections.
    def websocket_caller(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        server = websockets.serve(self.handle_websocket, '127.0.0.1', 8080)
        loop.run_until_complete(server)
        loop.run_forever()
        
    # Run WebSocket server in new thread.
    def start(self):
        server_thread = threading.Thread(target=self.websocket_caller, daemon=True)
        server_thread.start()

# Main method
def main():
    server = WebsocketServer()
    server.start()
    
    msg = ""
    while msg != "!":
        msg = input()
    
if __name__ == "__main__":
    main()