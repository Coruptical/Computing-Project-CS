from utils.serverhandler import WebsocketServer
from utils.databasehandler import DatabaseHandler
from utils.requesthandler import RequestHandler

# Set up data variables, these depend on the device I'm testing the server on
# Currently, these are the ones that run on the actual oracle cloud server.
DATABASE_NAME = "compsci_project"
DATABASE_USERNAME = "serveruser"
DATABASE_PASSWORD = "user5682#"

SERVER_ADDRESS = '0.0.0.0'

def main():
    """Main function. This is what we're going to call through python to run our server."""
    databaseHandler = DatabaseHandler('127.0.0.1', user=DATABASE_USERNAME, password=DATABASE_PASSWORD, database=DATABASE_NAME)
    
    websock_server = WebsocketServer(requestHandler=RequestHandler(databaseHandler), server_address=SERVER_ADDRESS)
    websock_server.start()
    
    m = ""
    while m != "!":
        m = input()

if __name__ == "__main__":
    main()