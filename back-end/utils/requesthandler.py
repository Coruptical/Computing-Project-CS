import utils.classutils as cutils
from utils.databasehandler import DatabaseHandler
import json
from websockets.legacy.server import WebSocketServerProtocol

class RequestHandler:
    _databaseHandler: DatabaseHandler = None
    
    def __init__(self, databaseHandler: DatabaseHandler):
        self._databaseHandler = databaseHandler
    
    async def handleRegisterRequest(self, data: dict, websocket: WebSocketServerProtocol):
        username = data['username']
        password = data['password']
        
        usernameExists = self._databaseHandler.userExists(username)
        if usernameExists:
            await websocket.send(json.dumps({'error': 'USERNAME_EXISTS'}))
            return
        
        salt = cutils.new_salt()
        password_hash = cutils.hash_password(salt, password)
        created = self._databaseHandler.createUser(username, cutils.encode64(salt), password_hash)
        
        if created:
            await websocket.send(json.dumps({'response': 'SUCCESS'}))
        else:
            await websocket.send(json.dumps({'error': 'FAILED'}))
        
    async def handleLoginRequest(self, data: dict, websocket: WebSocketServerProtocol) -> dict:
        username = data['username']
        password = data['password']
        print(password)
        
        response = {
            "success": False,
            "userID": ""
        }
        
        usernameExists = self._databaseHandler.userExists(username)
        if not usernameExists:
            await websocket.send(json.dumps({'error': 'USERNAME_NOT_EXIST'}))
            return response
        
        salt, passwordHash = self._databaseHandler.fetchPasswordAndSalt(username)
        passwordMatches = cutils.check_password(cutils.decode64(salt), passwordHash, password)
        if passwordMatches:
            print("Your password matches.")
            uuid = self._databaseHandler.getUUID(username)
            if uuid != None:
                response["userID"] = uuid 
                response["success"] = True
            await websocket.send(json.dumps({'response': 'LOGIN_SUCCESS'}))
        else:
            print("Password doesn't match")
            await websocket.send(json.dumps({'error': 'PASSWORD_INCORRECT'}))
        
        return response
            
    async def handleUserAddFriend(self, userID: str, data: dict, websocket: WebSocketServerProtocol):
        print(userID)
        print(data)
        targetUsername = data['targetUsername']
        
        usernameTargetExists = self._databaseHandler.userExists(targetUsername)
        if not usernameTargetExists:
            await websocket.send(json.dumps({'error': 'USERNAME_TARGET_NOT_EXIST'}))
            return
        
        targetID = self._databaseHandler.getUUID(targetUsername)
        friends = self._databaseHandler.getFriends(userID)
        print(friends)
        if targetID in friends:
            await websocket.send(json.dumps({'error': 'FRIEND_CONNECTION_EXISTS'}))
            return
        
        requestActive = self._databaseHandler.checkFriendRequest(userID, targetID)
        if requestActive:
            await websocket.send(json.dumps({'error': 'FRIEND_REQUEST_EXISTS'}))
            return
        self._databaseHandler.createFriendRequest(userID, targetID)   
        
    async def handleUserRemoveFriend(self, userID: str, data: dict, websocket: WebSocketServerProtocol):
        print(userID)
        print(data)
        targetUsername = data['targetUsername']
        
        usernameTargetExists = self._databaseHandler.userExists(targetUsername)
        if not usernameTargetExists:
            await websocket.send(json.dumps({'error': 'USERNAME_TARGET_NOT_EXIST'}))
            return
        
        targetID = self._databaseHandler.getUUID(targetUsername)
        friends = self._databaseHandler.getFriends(userID)
        print(friends)
        if targetID not in friends:
            await websocket.send(json.dumps({'error': 'FRIEND_CONNECTION_NOT_EXISTS'}))
            return
        
        success = self._databaseHandler.removeFriendConnection(userID, targetID)
        if success:
            await websocket.send(json.dumps({'response': 'FRIEND_CONNECTION_REMOVED'}))
    
    async def handleUserAcceptRequest(self, userID: str, data: dict, websocket: WebSocketServerProtocol):
        print(userID)
        print(data)
        targetUsername = data['targetUsername']
        
        usernameTargetExists = self._databaseHandler.userExists(targetUsername)
        if not usernameTargetExists:
            await websocket.send(json.dumps({'error': 'USERNAME_TARGET_NOT_EXIST'}))
            return
        
        targetID = self._databaseHandler.getUUID(targetUsername)
        friends = self._databaseHandler.getFriends(userID)
        print(friends)
        if targetID in friends:
            await websocket.send(json.dumps({'error': 'FRIEND_CONNECTION_EXISTS'}))
            return
        
        success = self._databaseHandler.createFriendConnection(userID, targetID)
        if success:
            print("Friendship created.")
        self._databaseHandler.setFriendRequestInactive(userID, targetID)
        await websocket.send(json.dumps({'response': 'FRIEND_REQUEST_ACCEPTED'}))
    
    async def handleUserDenyRequest(self, userID: str, data: dict, websocket: WebSocketServerProtocol):
        print(userID)
        print(data)
        targetUsername = data['targetUsername']
        
        usernameTargetExists = self._databaseHandler.userExists(targetUsername)
        if not usernameTargetExists:
            await websocket.send(json.dumps({'error': 'USERNAME_TARGET_NOT_EXIST'}))
            return
        
        targetID = self._databaseHandler.getUUID(targetUsername)
        friends = self._databaseHandler.getFriends(userID)
        print(friends)
        if targetID in friends:
            await websocket.send(json.dumps({'error': 'FRIEND_CONNECTION_EXISTS'}))
            return
        
        
        success = self._databaseHandler.setFriendRequestInactive(userID, targetID)
        if success:
            await websocket.send(json.dumps({'response': 'FRIEND_REQUEST_DENIED'}))
            
    async def handleUserMessage(self, userID: str, data: dict, websocket: WebSocketServerProtocol, connected_sockets: dict[str: WebSocketServerProtocol]):
        print(userID)
        print(data)
        targetUsername = data['targetUsername']
        
        usernameTargetExists = self._databaseHandler.userExists(targetUsername)
        if not usernameTargetExists:
            await websocket.send(json.dumps({'error': 'USERNAME_TARGET_NOT_EXIST'}))
            return
        
        targetID = self._databaseHandler.getUUID(targetUsername)
        targetSocket: WebSocketServerProtocol = None
        
        try:
            targetSocket = connected_sockets[targetID]
        except:
            pass
        
        print(targetSocket)
        if targetSocket == None:
            print(targetUsername, "is not online.")
            # TODO: Send this to the database for when this user is not online.
            
            message_created = self._databaseHandler.createMessage(userID, targetID, data['message'])
            print(message_created)
            return
        
        target_data = {
            'server_request': 'USER_MESSAGE',
            'userID': userID,
            'username': self._databaseHandler.getUsername(userID),
            'user_message': data['message']
        }
               
        await targetSocket.send(json.dumps(target_data))
        
        # Even though we sent them the data, we still need to create the record in the database. 
        # later, we have to check if this message is in the currently active chat, to determine whether the messages
        # have been read or not.
        message_created = self._databaseHandler.createMessage(userID, targetID, data['message'])
        if not message_created:
            print("Error while creating message.")
        