import websockets
import asyncio
import threading
import json
from utils.requesthandler import RequestHandler

from websockets.legacy.server import WebSocketServerProtocol

class WebsocketServer:
    # This set holds all of the active "clients" (WebSocket connections) that are communicating with the server.
    active_clients = set()
    
    authorised_clients: dict[str: WebSocketServerProtocol] = {}
    authorised_socketIDS: dict[WebSocketServerProtocol: str] = {}
    authorised_sockets: set[WebSocketServerProtocol] = set()
    
    AUTHORISED_REQUESTS = ["USER_ADD_FRIEND",
                           "USER_REMOVE_FRIEND",
                           "USER_MESSAGE",
                           "USER_ACCEPT_REQUEST",
                           "USER_DENY_REQUEST"]
    
    requestHandler: RequestHandler = None
    
    def __init__(self, requestHandler: RequestHandler):
        self.requestHandler = requestHandler

    def removeActiveSocket(self, websocket):
        self.active_clients.remove(websocket)
        userid = self.authorised_socketIDS[websocket]
        self.authorised_sockets.remove(websocket)
        self.authorised_clients.pop(userid)
        self.authorised_socketIDS.pop(websocket)
        print("WebSocket disconnected")        

    # This method is called when a websocket is connected to the server.
    async def handle_websocket(self, websocket: WebSocketServerProtocol, path):
        print("WebSocket connected")
        self.active_clients.add(websocket)
        try:
            while True:
                async for message in websocket:
                    data: dict = {}
                    
                    try:
                        data = json.loads(message)
                    except:
                        continue
                    
                    requestType = None
                    try:
                        requestType = data['requestType']
                    except:
                        continue
                    
                    if requestType in self.AUTHORISED_REQUESTS and websocket not in self.authorised_sockets:
                        await websocket.close()
                        self.active_clients.remove(websocket)
                        print("WebSocket connection closed due to unauthorised request.")
                        return
                    
                    if requestType == "REGISTER":
                        await self.requestHandler.handleRegisterRequest(data, websocket)
                    elif requestType == "LOGIN":
                        response = await self.requestHandler.handleLoginRequest(data, websocket)
                        if response['success'] == False:
                            continue
                        userID = response['userID']
                        self.authorised_clients[userID] = websocket
                        self.authorised_socketIDS[websocket] = userID
                        self.authorised_sockets.add(websocket)    
                    elif requestType == "USER_ADD_FRIEND":
                        await self.requestHandler.handleUserAddFriend(self.authorised_socketIDS[websocket], data, websocket)
                    elif requestType == "USER_ACCEPT_REQUEST":
                        await self.requestHandler.handleUserAcceptRequest(self.authorised_socketIDS[websocket], data, websocket)
                    elif requestType == "USER_DENY_REQUEST":
                        await self.requestHandler.handleUserDenyRequest(self.authorised_socketIDS[websocket], data, websocket)
                    elif requestType == "USER_REMOVE_FRIEND":
                        await self.requestHandler.handleUserRemoveFriend(self.authorised_socketIDS[websocket], data, websocket)
                    elif requestType == "USER_MESSAGE":
                        await self.requestHandler.handleUserMessage(self.authorised_socketIDS[websocket], data, websocket,
                                                                    self.authorised_clients)
                    elif requestType == "DISCONNECT":
                        userID = self.authorised_socketIDS[websocket]
                        if userID == None:
                            self.active_clients.remove(websocket)
                            websocket.close()
                            return
                        
                        self.removeActiveSocket(websocket)
                        await websocket.close()
                        return
                    else:
                        print(requestType)
        except websockets.ConnectionClosed:
            self.removeActiveSocket(websocket)
        
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