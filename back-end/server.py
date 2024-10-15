import socket

def main():
    host = "0.0.0.0"
    port = 8080
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host, port))
    sock.listen(5)
    
    c, addr = sock.accept()
    print(f"connection from {addr}")
    c.close()
    
if __name__ == "__main__":
    main()