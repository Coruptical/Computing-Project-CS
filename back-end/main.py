from utils.serverhandler import WebsocketServer

def main():
    websock_server = WebsocketServer()
    websock_server.start()
    
    m = ""
    while m != "!":
        m = input()

if __name__ == "__main__":
    main()