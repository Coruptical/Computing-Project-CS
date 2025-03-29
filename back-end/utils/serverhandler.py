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
    
    user_chats_open: dict[str: str] = {}
    
    AUTHORISED_REQUESTS = ["USER_ADD_FRIEND",
                           "USER_REMOVE_FRIEND",
                           "USER_MESSAGE",
                           "USER_ACCEPT_REQUEST",
                           "USER_DENY_REQUEST"]
    
    requestHandler: RequestHandler = None
    
    def __init__(self, requestHandler: RequestHandler, server_address: str):
        self.requestHandler = requestHandler
        self.server_address = server_address

    def removeActiveSocket(self, websocket):
        """Removes an active socket from all of our data lists."""
        self.active_clients.remove(websocket)
        userid = self.authorised_socketIDS[websocket]
        self.authorised_sockets.remove(websocket)
        self.authorised_clients.pop(userid)
        self.authorised_socketIDS.pop(websocket)

    async def handle_websocket(self, websocket: WebSocketServerProtocol):
        """This method is called when a websocket is connected to the server.
        It handles the incoming message (request, hopefully) from the socket
        After it determines which request we need to handle, it sends this over to the request handler to do the work.
        """
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
                        userID = None
                        try:
                            userID = self.authorised_socketIDS[websocket]
                        except:
                            pass
                        if userID == None:
                            self.active_clients.remove(websocket)
                        else:       
                            self.removeActiveSocket(websocket)
                        await websocket.close()
                        print("WebSocket disconnected")
                        return
                    elif requestType == "GET_FRIEND_LIST":
                        await self.requestHandler.handleGetFriendList(self.authorised_socketIDS[websocket], data, websocket)
                    elif requestType == "GET_FRIEND_REQUESTS":
                        await self.requestHandler.handleGetFriendRequests(self.authorised_socketIDS[websocket], data, websocket)
                    elif requestType == "GET_MESSAGES":
                        await self.requestHandler.handleGetMessages(self.authorised_socketIDS[websocket], data, websocket)
                    else:
                        print(requestType)
        except websockets.ConnectionClosed:
            userID = None
            try:
                userID = self.authorised_socketIDS[websocket]
            except:
                pass
            if userID == None:
                self.active_clients.remove(websocket)
            else:
                self.removeActiveSocket(websocket)
            print("WebSocket connection closed")
        
    
    def websocket_caller(self):
        """Creates a new loop to handle_websocket method to process new incoming connections.
        This will call the handle_websocket method for any incoming connection to this address.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def start_server():
            server = await websockets.serve(self.handle_websocket, self.server_address, 8080)
            return server
        server = loop.run_until_complete(start_server())
        loop.run_forever()
        
    
    def start(self):
        """Run WebSocket server in new thread.
        This allows our other program threads to do work while we are waiting for incoming connections.
        """
        server_thread = threading.Thread(target=self.websocket_caller, daemon=True)
        server_thread.start()
