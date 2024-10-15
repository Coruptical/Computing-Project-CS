class User:
    _userID: str
    _username: str
    _friends_list: list[str]
    
    def __init__(self, userID: str, username: str, friends_list:str) -> None:
        self._userID = userID
        self._username = username
        self._friends_list = friends_list
        
    def getUserID(self) -> str:
        return self._userID
    
    def getUsername(self) -> str:
        return self._username
        
    def getFriendsList(self) -> list[str]:
        return self._friends_list
        
    def setUsername(self, username: str) -> None:
        self._username = username