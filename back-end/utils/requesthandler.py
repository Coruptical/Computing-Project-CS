import utils.classutils as cutils
from utils.databasehandler import DatabaseHandler
import json
from websockets.legacy.server import WebSocketServerProtocol
from models.message import Message

class RequestHandler:
    """Request handler. Processes the data from all incoming requests, and returns responses to the client."""
    _databaseHandler: DatabaseHandler = None
    
    def __init__(self, databaseHandler: DatabaseHandler):
        """I need to access the database handler a lot to access data from the database."""
        self._databaseHandler = databaseHandler
    
    async def handleRegisterRequest(self, data: dict, websocket: WebSocketServerProtocol):
        """Attempts to register a new user with the given username. The password is salted and hashed, then stored.
        If the username already exists, the account will fail to be made and we return an error message back to the socket.
        """
        username = data['username']
        password = data['password']
        
        socket_response = {
            'responseSuccess': False,
            'request': data['requestType'],
            'message': ''
        }
        
        salt = cutils.new_salt()
        password_hash = cutils.hash_password(salt, password)
        
        usernameExists = self._databaseHandler.userExists(username)
        if usernameExists:
            socket_response['message'] = 'USERNAME_EXISTS'
        else:
            created = self._databaseHandler.createUser(username, cutils.encode64(salt), password_hash)
            if created: 
                socket_response['responseSuccess'] = True
            else:
                socket_response['message'] = 'UNKNOWN_FAILED'
        
        await websocket.send(json.dumps(socket_response))
        
    async def handleLoginRequest(self, data: dict, websocket: WebSocketServerProtocol) -> dict:
        """Attempts to login a new user with the given username and password.
        If the username doesn't exist, we return an error message back to the socket.
        The password salt and hash is gotten from the database.
        We salt and hash the given password and compare them. If they're the same the socket is authenticated.
        """
        username = data['username']
        password = data['password']
        
        response = {
            "success": False,
            "userID": ""
        }
        socket_response = {
            'responseSuccess': False,
            'request': data['requestType'],
            'message': ''
        }
        usernameExists = self._databaseHandler.userExists(username)
        if not usernameExists:
            socket_response['message'] = 'USERNAME_NOT_EXIST'
        else:
            salt, passwordHash = self._databaseHandler.fetchPasswordAndSalt(username)
            passwordMatches = cutils.check_password(cutils.decode64(salt), passwordHash, password)
            if passwordMatches:
                print(f"{username}'s password matches.")
                uuid = self._databaseHandler.getUUID(username)
                if uuid != None:
                    response["userID"] = uuid 
                    response["success"] = True
                socket_response['responseSuccess'] = True
            else:
                print(f"{username}'s password doesn't match")
                socket_response['message'] = 'PASSWORD_INCORRECT'
        
        await websocket.send(json.dumps(socket_response))
        return response
            
    async def handleUserAddFriend(self, userID: str, data: dict, websocket: WebSocketServerProtocol):
        """Attempts to create a friend request between the user and another given user.
        We return an error message back to the socket if:
        - The given username doesn't exist
        - The two users are already friends
        - This friend request is already active (exists)
        If not, the database handler then creates an active friend request.
        """
        targetUsername = data['targetUsername']
        
        socket_response = {
            'responseSuccess': False,
            'request': data['requestType'],
            'message': ''
        }
        
        usernameTargetExists = self._databaseHandler.userExists(targetUsername)
        if not usernameTargetExists:
            socket_response['message'] = 'USERNAME_NOT_EXISTS'
            await websocket.send(json.dumps(socket_response))
            return
        
        targetID = self._databaseHandler.getUUID(targetUsername)
        friends = self._databaseHandler.getFriends(userID)
        if targetID in friends:
            socket_response['message'] = 'FRIEND_CONNECTION_EXISTS'
            await websocket.send(json.dumps(socket_response))
            return
        
        requestActive = self._databaseHandler.checkFriendRequest(userID, targetID)
        if requestActive:
            socket_response['message'] = 'FRIEND_REQUEST_EXISTS'
            await websocket.send(json.dumps(socket_response))
            return
        
        requestActive = self._databaseHandler.checkFriendRequest(targetID, userID)
        if requestActive:
            socket_response['message'] = 'FRIEND_REQUEST_EXISTS'
            await websocket.send(json.dumps(socket_response))
            return
        
        socket_response['responseSuccess'] = True
        self._databaseHandler.createFriendRequest(userID, targetID)
        await websocket.send(json.dumps(socket_response))
        
        
    async def handleUserRemoveFriend(self, userID: str, data: dict, websocket: WebSocketServerProtocol):
        """Attempts to remove the friend connection between the user and the target user.
        We return an error message back to the socket if:
        - The username target doesn't exist
        - The two users are already not friends
        If not, the friend connection is removed (set to in-active).
        """
        targetUsername = data['targetUsername']
        
        socket_response = {
            'responseSuccess': False,
            'request': data['requestType'],
            'message': ''
        }
        
        usernameTargetExists = self._databaseHandler.userExists(targetUsername)
        if not usernameTargetExists:
            socket_response['message'] = "USERNAME_TARGET_NOT_EXIST"
            await websocket.send(json.dumps(socket_response))
            return
        
        targetID = self._databaseHandler.getUUID(targetUsername)
        friends = self._databaseHandler.getFriends(userID)
        if targetID not in friends:
            socket_response['message'] = "FRIEND_CONNECTION_NOT_EXISTS"
            await websocket.send(socket_response)
            return
        
        success = self._databaseHandler.removeFriendConnection(userID, targetID)
        if success:
            socket_response['responseSuccess'] = True
        
        await websocket.send(json.dumps(socket_response))
    
    async def handleUserAcceptRequest(self, userID: str, data: dict, websocket: WebSocketServerProtocol):
        """Attempts to handle a user accepting a friend request from another user.
        We return an error message back to the socket if:
        - The target username doesn't exist
        - The two users are already friends
        If not, the friend connection is established by the database handler between the two users.
        """
        targetUsername = data['targetUsername']
        
        socket_response = {
            'responseSuccess': False,
            'request': data['requestType'],
            'message': ''
        }
        
        usernameTargetExists = self._databaseHandler.userExists(targetUsername)
        if not usernameTargetExists:
            socket_response['message']= "USERNAME_TARGET_NOT_EXIST"
        else:
            targetID = self._databaseHandler.getUUID(targetUsername)
            friends = self._databaseHandler.getFriends(userID)
            if targetID in friends:
                socket_response['message']= 'FRIEND_CONNECTION_EXISTS'
                await websocket.send(json.dumps(socket_response))
        
        success = self._databaseHandler.createFriendConnection(userID, targetID)
        if success:
            socket_response['responseSuccess'] = True
        
        self._databaseHandler.setFriendRequestInactive(userID, targetID)
        await websocket.send(json.dumps(socket_response))
    
    async def handleUserDenyRequest(self, userID: str, data: dict, websocket: WebSocketServerProtocol):
        """Attempts to handle a user denying a friend request from another user.
        We return an error message back to the socket if:
        - The target username doesn't exist
        - The two users are already friends
        If not, no friend connection is established and the request gets removed (becomes in-active).
        """
        targetUsername = data['targetUsername']
    
        socket_response = {
            'responseSuccess': False,
            'request': data['requestType'],
            'message': ''
        }        
        
        
        usernameTargetExists = self._databaseHandler.userExists(targetUsername)
        if not usernameTargetExists:
            socket_response['message']= "USERNAME_TARGET_NOT_EXIST"
        else:
            targetID = self._databaseHandler.getUUID(targetUsername)
            friends = self._databaseHandler.getFriends(userID)
            if targetID in friends:
                socket_response['message']= 'FRIEND_CONNECTION_EXISTS'
                await websocket.send(json.dumps(socket_response))
                
        success = self._databaseHandler.setFriendRequestInactive(userID, targetID)
        if success:
            socket_response['responseSuccess'] = True
            
        await websocket.send(json.dumps(socket_response))
    
    async def handleUserMessage(self, userID: str, data: dict, websocket: WebSocketServerProtocol, connected_sockets: dict[str: WebSocketServerProtocol]):
        """Attempts to handle the sending of a message from one user to another.
        We return an error message back to the socket if:
        - The username target doesn't exist
        - The message isn't created for an external reason
        We check the list of connected sockets to check if the target user is online.
        If they are, we can send them an incoming message from this user.
        If they're not, the message gets stored by the database handler.
        """
        targetUsername = data['targetUsername']
        
        socket_response = {
            'responseSuccess': False,
            'request': data['requestType'],
            'message': ''
        }           
        
        targetSocket: WebSocketServerProtocol = None
        targetID = None
        
        usernameTargetExists = self._databaseHandler.userExists(targetUsername)
        if not usernameTargetExists:
            socket_response['message']= 'USERNAME_TARGET_NOT_EXIST'
        else:
            targetID = self._databaseHandler.getUUID(targetUsername)
            
            message_created = self._databaseHandler.createMessage(userID, targetID, data['message'])
            if not message_created:
                print("Error while creating message.")
                socket_response['message'] = 'ERROR_CREATING_MESSAGE'
            else:
                socket_response['responseSuccess'] = True
            
            try:
                targetSocket = connected_sockets[targetID]
                
                # Set up data to send to target user
                targetMessage = self._databaseHandler.getLastMessage(userID, targetID)

                target_data = {
                    'responseSuccess': True,
                    'request': 'INCOMING_MESSAGE',
                    'message': json.dumps(targetMessage, default=lambda x: x.__dict__)  
                }
                
                await targetSocket.send(json.dumps(target_data))
            except:
                pass
                
        
        await websocket.send(json.dumps(socket_response))
        
    async def handleGetFriendList(self, userID: str, data: dict, websocket: WebSocketServerProtocol):
        """Attempts to get the friend list of a user.
        Calls the database handler, and sends the friend list back to the socket.
        """
        friends = self._databaseHandler.getFriendList(userID)
    
        
        socket_response = {
            'responseSuccess': False,
            'request': data['requestType'],
            'message': ''
        }
        
        if friends != None:
            socket_response['responseSuccess'] = True
            socket_response['message'] = json.dumps(friends)
            
        await websocket.send(json.dumps(socket_response))
        
    async def handleGetFriendRequests(self, userID: str, data:dict, websocket: WebSocketServerProtocol):
        """Attempts to get a user's friend requests.
        Calls the database handler, and sends the friend requests back to the socket.
        """
        socket_response = {
            'responseSuccess': False,
            'request': data['requestType'],
            'message': ''
        } 
        
        requests = self._databaseHandler.getFriendRequests(userID)
        
        if requests != None:
            socket_response['responseSuccess'] = True
            socket_response['message'] = json.dumps(requests)
        
        await websocket.send(json.dumps(socket_response))
        
    async def handleGetMessages(self, userID: str, data: dict, websocket: WebSocketServerProtocol):
        """Attempts to get all the message of a user.
        Sets the page number (which is determined by the client)
        Calls the database handler to get the messages up to that page number
        Returns the messages to the socket.
        """
        page = data['page']
        friendName = data['friendName']
        
        socket_response = {
            'responseSuccess': False,
            'request': data['requestType'],
            'message': ''
        }
        
        messages: list[Message] = self._databaseHandler.getUserMessages(userID, friendName, page)
        
        if messages != None:
            socket_response['responseSuccess'] = True
            socket_response['message'] = json.dumps(messages, default=lambda x: x.__dict__)
            
        await websocket.send(json.dumps(socket_response))
    