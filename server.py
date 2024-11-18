import threading
import socket

IP = "127.0.0.1" #socket.gethostbyname(socket.gethostname())
PORT = 3300
BUFFER_SIZE = 1024
FORMAT = "utf-8"

ADDR = (IP, PORT)

def logon(connection: socket) -> bool:
    data = connection.recv(1024).decode(FORMAT)
    return data == "LOGON"

def handle_connection(connection: socket, address):

    print(f"[*] Established connection: {address}")

    if not logon(connection):
        connection.send("ERR".encode(FORMAT))
        connection.close()
        print(f"[*] Connection closed: {address}")
        return

    connection.send("OK".encode(FORMAT))

    while True:
        data = connection.recv(BUFFER_SIZE).decode("utf-8")

        command = data.split(' ')

        if data == "LOGOUT":
            break

        connection.send(f"---> {data}".encode("utf-8"))

    connection.close()
    print(f"[*] Connection closed: {address}")


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