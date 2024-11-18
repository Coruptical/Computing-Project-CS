import utils.classutils as cutils
from utils.databasehandler import DatabaseHandler
import json

from websockets.legacy.server import WebSocketServerProtocol

class RequestHandler:
    _databaseHandler: DatabaseHandler = None
    
    def __init__(self, databaseHandler: DatabaseHandler):
        self._databaseHandler = databaseHandler
    
    # TODO: Create pseudocode for this since we're classing this as larger "algorithm"
    
    # TODO: Talk about the error I got while trying to fix the password comparisons
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
            
    async def handleLoginRequest(self, data: dict, websocket: WebSocketServerProtocol):
        username = data['username']
        password = data['password']
        print(password)
        
        usernameExists = self._databaseHandler.userExists(username)
        if not usernameExists:
            await websocket.send(json.dumps({'error': 'USERNAME_NOT_EXIST'}))
            return
        
        salt, passwordHash = self._databaseHandler.fetchPasswordAndSalt(username)
        passwordMatches = cutils.check_password(cutils.decode64(salt), passwordHash, password)
        if passwordMatches:
            print("Your password matches.")
        else:
            print("Password doesn't match")