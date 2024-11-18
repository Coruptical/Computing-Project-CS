import mysql.connector as mysql
from mysql.connector import MySQLConnection
import uuid

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
        
    # TODO: Write about the error this caused, how the try/except caused it to get lost and how I had to manually look for it and use decode instead.
    def fetchPasswordAndSalt(self, username: str) -> tuple[bytes, bytes]:
        cursor = self.getDatabase().cursor()
        cursor.execute(f'SELECT passwordSalt, password FROM users WHERE username=\"{username}\"')
        result = cursor.fetchone()
        return (result[0], result[1])