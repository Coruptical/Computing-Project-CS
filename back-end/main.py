from utils.serverhandler import WebsocketServer
from utils.databasehandler import DatabaseHandler
from utils.requesthandler import RequestHandler

DATABASE_NAME = "csproject_database"
DATABASE_USERNAME = "csuser"
DATABASE_PASSWORD = "user5682#"
SERVER_ADDRESS = '10.14.32.106'

def main():
    databaseHandler = DatabaseHandler('127.0.0.1', user=DATABASE_USERNAME, password=DATABASE_PASSWORD, database=DATABASE_NAME)
    
    websock_server = WebsocketServer(requestHandler=RequestHandler(databaseHandler), server_address=SERVER_ADDRESS)
    websock_server.start()
    
    m = ""
    while m != "!":
        m = input()

if __name__ == "__main__":
    main()