class Message:
    username: str = None
    body: str = None
    timestamp: str = None
    
    def __init__(self, username, body, timestamp):
        self.username = username
        self.body = body
        self.timestamp = timestamp