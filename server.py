import threading
import socket

IP = socket.gethostbyname(socket.gethostname())
PORT = 3300
BUFFER_SIZE = 1024
FORMAT = "utf-8"

ADDR = (IP, PORT)

def handle_connection(connection, address):

    print(f"[*] Established connection: {address}")

    connection.send("OK".encode(FORMAT))

    connection.close()
    print(f"[*] Connection close: {address}")


def main():
    print("[*] Starting Server...")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)
    server.listen()

    server.settimeout(1.0)

    print(f"[*] Server is listening on {IP}:{PORT}")

    while True:
        try:
            (connection, address) = server.accept()

            thread = threading.Thread(target=handle_connection, args=(connection, address))

            thread.start()
        
        except socket.timeout:
            pass



if __name__ == "__main__":
    main()