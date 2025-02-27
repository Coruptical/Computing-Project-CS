import mysql.connector as mysql
from mysql.connector import MySQLConnection
import uuid
from models.message import Message

class DatabaseHandler:
    _database: MySQLConnection = None
    
    def __init__(self, host: str, user: str, password: str):
        self._database = mysql.connect(host=host, user=user, password=password)
        
    def getDatabase(self) -> MySQLConnection:
        return self._database
    
    def setDatabase(self, database: str) -> None:
        self.getDatabase().cursor().execute(f"USE {database}")
    
    def userExists(self, username: str) -> bool:
        cursor = self.getDatabase().cursor()
        cursor.execute(f"SELECT userID FROM users WHERE username=\"{username}\"")
        
        result = cursor.fetchall()
        for x in result:
            return True
        return False
    
    def createUser(self, username: str, passwordSalt: str, password: str) -> bool:
        cursor = self.getDatabase().cursor()
        userID = uuid.uuid4()
        try:
            cursor.execute(f"INSERT INTO users VALUES (\"{userID}\", \"{username}\", \"{passwordSalt}\", \"{password}\")")
            self.getDatabase().commit()
            return True
        except: 
            return False
        
    def fetchPasswordAndSalt(self, username: str) -> tuple[bytes, bytes]:
        cursor = self.getDatabase().cursor()
        cursor.execute(f'SELECT passwordSalt, password FROM users WHERE username=\"{username}\"')
        result = cursor.fetchone()
        return (result[0], result[1])
    
    def getUUID(self, username: str) -> str:
        cursor = self.getDatabase().cursor()
        try:
            cursor.execute(f'SELECT userID FROM users WHERE username=\"{username}\"')
            result = cursor.fetchone()
            return result[0]
        except:
            return None
        
    def getUsername(self, userID: str) -> str:
        cursor = self.getDatabase().cursor()
        try:
            cursor.execute(f'SELECT username FROM users WHERE userID=\"{userID}\"')
            result = cursor.fetchone()
            return result[0]
        except:
            return None
        
    def getFriends(self, userID: str) -> list[str]:
        friends = []
        cursor = self.getDatabase().cursor()
        cursor.execute(f"SELECT friendID FROM friendship WHERE userID=\"{userID}\" AND connectionActive=TRUE")
        result = cursor.fetchall()
        for row in result:
            friends.append(row[0])
        return friends
    
    def getFriendList(self, userID: str) -> list[str]:
        friends = []
        cursor = self.getDatabase().cursor()
        stmt = f"""
        SELECT users.username
        FROM users
        JOIN friendship ON users.userID=friendship.friendID WHERE friendship.userID=\"{userID}\" AND friendship.connectionActive=TRUE
        """
        cursor.execute(stmt)
        for x in cursor:
            friends.append(x[0])
        return friends
    
    def getFriendRequests(self, userID: str) -> list[str]:
        requests = []
        cursor = self.getDatabase().cursor()
        stmt = f"""
        SELECT users.username
        FROM users
        JOIN friend_request ON users.userID=friend_request.sender_id WHERE recipient_id=\"{userID}\" AND friend_request.isActive=TRUE
        """
        cursor.execute(stmt)
        for x in cursor:
            requests.append(x[0])
        return requests
        
    def createFriendConnection(self, userID: str, targetID: str) -> bool:
        try:
            cursor = self.getDatabase().cursor()
            data = [(userID, targetID), (targetID, userID)]
            stmt = "INSERT INTO friendship(userID, friendID) VALUES(%s, %s)"
            cursor.executemany(stmt, data)
            self.getDatabase().commit()
            return True
        except:
            return False
        
    def removeFriendConnection(self, userID: str, targetID: str) -> bool:
        cursor = self.getDatabase().cursor()
        data = [(userID, targetID), (targetID, userID)]
        stmt = "UPDATE friendship SET connectionActive=0 WHERE connectionActive=1 AND userID=%s AND friendID=%s"
        cursor.executemany(stmt, data)
        self.getDatabase().commit()
        return True
        
    def setFriendRequestInactive(self, recipientID: str, senderID: str) -> bool:
        try:
            cursor = self.getDatabase().cursor()
            cursor.execute(f"UPDATE friend_request SET isActive=0 WHERE isActive=1 AND recipient_id=\"{recipientID}\" AND sender_id=\"{senderID}\"")
            self.getDatabase().commit()
            return True
        except:
            return False
        
    def createFriendRequest(self, userID: str, targetID: str) -> bool:
        cursor = self.getDatabase().cursor()
        cursor.execute(f"INSERT INTO friend_request(recipient_id, sender_id) VALUES(\"{targetID}\", \"{userID}\")")
        self.getDatabase().commit()
        
    def checkFriendRequest(self, userID: str, targetID: str) -> bool:
        cursor = self.getDatabase().cursor()
        cursor.execute(f"SELECT id FROM friend_request WHERE recipient_id=\"{targetID}\" AND sender_id=\"{userID}\" AND isActive=TRUE")
        
        result = cursor.fetchall()
        for x in result:
            return True
        return False
    
    def createMessage(self, userID: str, recipientID: str, message: str) -> bool:
        try:
            cursor = self.getDatabase().cursor()
            cursor.execute(f"INSERT INTO message(sender_id, body) VALUES(\"{userID}\", \"{message}\")")
            self.getDatabase().commit()
            
            cursor.execute(f"SELECT LAST_INSERT_ID()")
            result = cursor.fetchone()
            
            message_id = result[0]
            cursor.execute(f"INSERT INTO message_recipient(recipient_id, message_id, is_read) VALUES(\"{recipientID}\", \"{message_id}\", FALSE)")
            self.getDatabase().commit()
            return True
        except:
            return False
        
    def getUserMessages(self, userID: str, friendName: str, page: int) -> list[Message]:
        try: 
            friendID = self.getUUID(friendName)
            cursor = self.getDatabase().cursor()
            
            messages: list[Message] = []
        
            stmt = f"""
SELECT users.username, message.body, message.timestamp
FROM message
JOIN message_recipient ON message.id=message_recipient.message_id
JOIN users ON message.sender_id=users.userID
WHERE (message.sender_id=\"{userID}\" AND message_recipient.recipient_id=\"{friendID}\")
OR (message.sender_id=\"{friendID}\" AND message_recipient.recipient_id=\"{userID}\")
ORDER BY message.timestamp
LIMIT {page*50},{(page+1)*50}
            """
            cursor.execute(stmt)
            for row in cursor:
                username = row[0]
                body = row[1]
                timestamp = str(row[2])
                
                
                print(username, body, timestamp)
                messages.append(Message(username, body, timestamp))
                
            return messages
        except:
            return None
        
    def getLastMessage(self, userID: str, targetID: str) -> Message:
        try: 
            cursor = self.getDatabase().cursor()
            
            message: Message = None
        
            stmt = f"""
SELECT users.username, message.body, message.timestamp
FROM message
JOIN message_recipient ON message.id=message_recipient.message_id
JOIN users ON message.sender_id=users.userID
WHERE (message.sender_id=\"{userID}\" AND message_recipient.recipient_id=\"{targetID}\")
ORDER BY message.timestamp DESC
LIMIT 1
            """
            cursor.execute(stmt)
            for row in cursor:
                username = row[0]
                body = row[1]
                timestamp = str(row[2])
                
                
                print(username, body, timestamp)
                message = Message(username, body, timestamp)
                break
                
            return message
        except:
            return None