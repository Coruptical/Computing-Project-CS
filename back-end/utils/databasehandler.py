import mysql.connector as mysql
from mysql.connector import MySQLConnection
import uuid
from models.message import Message

class DatabaseHandler:
    _database: MySQLConnection = None
    
    
    def __init__(self, host: str, user: str, password: str, database: str, pool_size=16):
        """Initialise database connection pool"""
        self.db_config = {
            "host": host,
            "user": user,
            "password": password,
            "database": database
        }
        
        self.connection_pool = mysql.pooling.MySQLConnectionPool(
            pool_name="csproject_pool",
            pool_size=pool_size,
            **self.db_config
        )
    
    def get_connection(self) -> MySQLConnection:
        """Retrieve a connection from the pool."""
        try:
            conn = self.connection_pool.get_connection()
            if not conn.is_connected():
                conn.reconnect(attempts=3, delay=1)
            return conn
        except mysql.Error as err:
            print(f"Database connection error: {err}")
            return None
        
    def close_connection(self, conn: MySQLConnection):
        """Close the connection to the pool."""
        if conn and conn.is_connected():
            conn.close()
    
    def userExists(self, username: str) -> bool:
        """Check if a user exists in the database by their username."""
        conn = self.get_connection()
        
        if conn == None:
            return False
        
        
        cursor = conn.cursor()
        try:
            cursor.execute(f"SELECT userID FROM users WHERE username=\"{username}\"")
            
            result = cursor.fetchall()
            for x in result:
                return True
            return False
        finally:
            cursor.close()
            self.close_connection(conn)
    
    def createUser(self, username: str, passwordSalt: str, password: str) -> bool:
        """Create a new user in the database."""
        conn = self.get_connection()
        
        if conn == None:
            return False
        
        cursor = conn.cursor()
        userID = uuid.uuid4()
        try:
            cursor.execute(f"INSERT INTO users VALUES (\"{userID}\", \"{username}\", \"{passwordSalt}\", \"{password}\")")
            conn.commit()
            return True
        except: 
            return False
        finally:
            cursor.close()
            self.close_connection(conn)
        
    def fetchPasswordAndSalt(self, username: str) -> tuple[bytes, bytes]:
        """Get the password hash and salt for a given username."""
        conn = self.get_connection()
        
        if conn == None:
            return False
        
        cursor = conn.cursor()
        try:
            cursor.execute(f'SELECT passwordSalt, password FROM users WHERE username=\"{username}\"')
            result = cursor.fetchone()
            return (result[0], result[1])
        finally:
            cursor.close()
            self.close_connection(conn)
        
    def getUUID(self, username: str) -> str:
        """Get the UUID of a user by their username"""
        conn = self.get_connection()
        
        if conn == None:
            return None
        
        cursor = conn.cursor()
        try:
            cursor.execute(f'SELECT userID FROM users WHERE username=\"{username}\"')
            result = cursor.fetchone()
            return result[0]
        except:
            return None
        finally:
            cursor.close()
            self.close_connection(conn)
        
    def getUsername(self, userID: str) -> str:
        """Get the username of a user by their UUID"""
        conn = self.get_connection()
        
        if conn == None:
            return None
        
        cursor = conn.cursor()
        try:
            cursor.execute(f'SELECT username FROM users WHERE userID=\"{userID}\"')
            result = cursor.fetchone()
            return result[0]
        except:
            return None
        finally:
            cursor.close()
            self.close_connection(conn)
    
    def getFriends(self, userID: str) -> list[str]:
        """Get a list of friend IDs for the given user ID."""
        conn = self.get_connection()
        
        if conn == None:
            return None        
        
        
        friends = []
        cursor = conn.cursor()
        try:
            cursor.execute(f"SELECT friendID FROM friendship WHERE userID=\"{userID}\" AND connectionActive=TRUE")
            result = cursor.fetchall()
            for row in result:
                friends.append(row[0])
            return friends
        finally:
            cursor.close()
            self.close_connection(conn)
    
    def getFriendList(self, userID: str) -> list[str]:
        """Get a friend list of users for the given user ID."""
        conn = self.get_connection()
        
        if conn == None:
            return None
        
        friends = []
        cursor =  conn.cursor()
        try:
            stmt = f"""
            SELECT users.username
            FROM users
            JOIN friendship ON users.userID=friendship.friendID WHERE friendship.userID=\"{userID}\" AND friendship.connectionActive=TRUE
            """
            cursor.execute(stmt)
            for x in cursor:
                friends.append(x[0])
            return friends
        finally:
            cursor.close()
            self.close_connection(conn)
    
    def getFriendRequests(self, userID: str) -> list[str]:
        """Get a list of friend requests for the given user ID."""
        conn = self.get_connection()
        
        if conn == None:
            return None
        
        requests = []
        cursor = conn.cursor()
        try:
            stmt = f"""
            SELECT users.username
            FROM users
            JOIN friend_request ON users.userID=friend_request.sender_id WHERE recipient_id=\"{userID}\" AND friend_request.isActive=TRUE
            """
            cursor.execute(stmt)
            for x in cursor:
                requests.append(x[0])
            return requests
        finally:
            cursor.close()
            self.close_connection(conn)
            
    def createFriendConnection(self, userID: str, targetID: str) -> bool:
        """Create a friend connection in the friendship database table."""
        conn = self.get_connection()
        
        if conn == None:
            return False        
        
        try:
            cursor = conn.cursor()
            data = [(userID, targetID), (targetID, userID)]
            stmt = "INSERT INTO friendship(userID, friendID) VALUES(%s, %s)"
            cursor.executemany(stmt, data)
            conn.commit()
            return True
        except:
            return False
        finally:
            cursor.close()
            self.close_connection(conn)
        
    def removeFriendConnection(self, userID: str, targetID: str) -> bool:
        """Set a friend connection to inactive, effectively removing that connection."""
        conn = self.get_connection()
        
        if conn == None:
            return False
        
        cursor = conn.cursor()
        try:
            data = [(userID, targetID), (targetID, userID)]
            stmt = "UPDATE friendship SET connectionActive=0 WHERE connectionActive=1 AND userID=%s AND friendID=%s"
            cursor.executemany(stmt, data)
            conn.commit()
            return True
        finally:
            cursor.close()
            self.close_connection(conn)
            
    def setFriendRequestInactive(self, recipientID: str, senderID: str) -> bool:
        """Set a friend request to inactive, effectively removing that friend request."""
        conn = self.get_connection()
        
        if conn == None:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE friend_request SET isActive=0 WHERE isActive=1 AND recipient_id=\"{recipientID}\" AND sender_id=\"{senderID}\"")
            conn.commit()
            return True
        except:
            return False
        finally:
            cursor.close()
            self.close_connection(conn)
            
    def createFriendRequest(self, userID: str, targetID: str) -> bool:
        """Create a friend request between two users, given the user ID and target ID."""
        conn = self.get_connection()
        
        if conn == None:
            return False
        
        cursor = conn.cursor()
        try:
            cursor.execute(f"INSERT INTO friend_request(recipient_id, sender_id) VALUES(\"{targetID}\", \"{userID}\")")
            conn.commit()
        finally:
            cursor.close()
            self.close_connection(conn)
        
    def checkFriendRequest(self, userID: str, targetID: str) -> bool:
        """Check if a friend request is active between a user ID and a friend ID."""
        conn = self.get_connection()
        
        if conn == None:
            return False        
        
        cursor = conn.cursor()
        try:
            cursor.execute(f"SELECT id FROM friend_request WHERE recipient_id=\"{targetID}\" AND sender_id=\"{userID}\" AND isActive=TRUE")
            
            result = cursor.fetchall()
            for x in result:
                return True
            return False
        finally:
            cursor.close()
            self.close_connection(conn)
    
    def createMessage(self, userID: str, recipientID: str, message: str) -> bool:
        """Store a message sent by a user ID and link it to a recipient ID."""
        conn = self.get_connection()
        
        if conn == None:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute(f"INSERT INTO message(sender_id, body) VALUES(\"{userID}\", \"{message}\")")
            conn.commit()
            
            cursor.execute(f"SELECT LAST_INSERT_ID()")
            result = cursor.fetchone()
            
            message_id = result[0]
            cursor.execute(f"INSERT INTO message_recipient(recipient_id, message_id, is_read) VALUES(\"{recipientID}\", \"{message_id}\", FALSE)")
            conn.commit()
            return True
        except:
            return False
        finally:
            cursor.close()
            self.close_connection(conn)
        
    def getUserMessages(self, userID: str, friendName: str, page: int) -> list[Message]:
        """Get a shortened list of all of the messages that a user has with a friend, given the user ID and friend name."""
        conn = self.get_connection()
        
        if conn == None:
            return None
        
        try: 
            friendID = self.getUUID(friendName)
            cursor = conn.cursor()
            
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
        finally:
            cursor.close()
            self.close_connection(conn)
        
    def getLastMessage(self, userID: str, targetID: str) -> Message:
        """Get the last message that was exchanged between two users, given the user ID and target ID."""
        conn = self.get_connection()
        
        if conn == None:
            return None
        
        try: 
            cursor = conn.cursor()
            
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
        finally:
            cursor.close()
            self.close_connection(conn)