import utils.classutils as cutils
from utils.databasehandler import DatabaseHandler
import json
from websockets.legacy.server import WebSocketServerProtocol
from models.message import Message

class RequestHandler:
    _databaseHandler: DatabaseHandler = None
    
    def __init__(self, databaseHandler: DatabaseHandler):
        self._databaseHandler = databaseHandler
    
    async def handleRegisterRequest(self, data: dict, websocket: WebSocketServerProtocol):
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
        username = data['username']
        password = data['password']
        print(data)
        
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
        print(userID)
        print(data)
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
        print(friends)
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
        print(userID)
        print(data)
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
            print("Friendship created.")
            socket_response['responseSuccess'] = True
        
        self._databaseHandler.setFriendRequestInactive(userID, targetID)
        await websocket.send(json.dumps(socket_response))
    
    async def handleUserDenyRequest(self, userID: str, data: dict, websocket: WebSocketServerProtocol):
        print(userID)
        print(data)
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
    
    # TODO: Send response to tell user that the target user isn't friends with them.
    async def handleUserMessage(self, userID: str, data: dict, websocket: WebSocketServerProtocol, connected_sockets: dict[str: WebSocketServerProtocol]):
        print(userID)
        print(data)
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
        
            try:
                targetSocket = connected_sockets[targetID]
            
            except:
                pass
        
            message_created = self._databaseHandler.createMessage(userID, targetID, data['message'])
            if not message_created:
                print("Error while creating message.")
                socket_response['message'] = 'ERROR_CREATING_MESSAGE'
            else:
                socket_response['responseSuccess'] = True
        
        await websocket.send(json.dumps(socket_response))
        
    async def handleGetFriendList(self, userID: str, data: dict, websocket: WebSocketServerProtocol):
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
    
    async def handleUserChatOpen(self, userID: str, data: dict, websocket: WebSocketServerProtocol):
        pass