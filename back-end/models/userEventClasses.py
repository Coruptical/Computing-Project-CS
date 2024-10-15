from user import User
from datetime import datetime

class UserMessage:
    _content: str
    _timestamp: datetime
    
    def __init__(self, content: str, timestamp: datetime):
        self._content = content
        self._timestamp = timestamp
        
    def getContent(self) -> str:
        return self._content
    
    def getTimestamp(self) -> datetime:
        return self._timestamp

class UserEvent:
    _user: User
    
    def __init__(self, user: User):
        self._user = user
        
    def getUser(self) -> User:
        return self._user

class UserRegisterEvent(UserEvent):
    _registerTimestamp: datetime
    
    def __init__(self, user: User, registerTimestamp: datetime):
        super().__init__(user)
        self._registerTimestamp = registerTimestamp
        
    def handle(self):
        pass   
    
class UserMessageEvent(UserEvent):
    _message: UserMessage
    
    def __init__(self, user):
        super().__init__(user)
         
    def handle(self):
        pass
    
class UserLoginEvent(UserEvent):
    _loginTimestamp: datetime
    
    def __init__(self, user):
        super().__init__(user)
        
    def handle(self):
        pass
    
class UserAddFriendEvent(UserEvent):
    _targetID: str
    
    def __init__(self, user):
        super().__init__(user)
        
    def handle(self):
        pass
    
class UserRemoveFriendEvent(UserEvent):
    _targetID: str
    
    def __init__(self, user):
        super().__init__(user)
        
    def handle(self):
        pass
    
class UserAcceptFriendEvent(UserEvent):
    _targetID: str
    
    def __init__(self, user):
        super().__init__(user)
        
    def handle(self):
        pass
    
class UserDenyFriendEvent(UserEvent):
    _targetID: str
    
    def __init__(self, user):
        super().__init__(user)
        
    def handle(self):
        pass