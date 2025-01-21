from utils.serverhandler import WebsocketServer
from utils.databasehandler import DatabaseHandler
from utils.requesthandler import RequestHandler

DATABASE_NAME = "csproject_database"
DATABASE_USERNAME = "csuser"
DATABASE_PASSWORD = "user5682#"

def main():
    databaseHandler = DatabaseHandler('127.0.0.1', user=DATABASE_USERNAME, password=DATABASE_PASSWORD)
    databaseHandler.setDatabase("csproject_database")
    
    websock_server = WebsocketServer(requestHandler=RequestHandler(databaseHandler))
    websock_server.start()
    
    databaseHandler.getFriendList("f6d60636-456f-4466-b1d7-7f5a93001a05")
    
    m = ""
    while m != "!":
        m = input()

if __name__ == "__main__":
    main()