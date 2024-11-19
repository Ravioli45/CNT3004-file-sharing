import threading
import socket
from pathlib import Path

IP = socket.gethostbyname(socket.gethostname())
PORT = 3300
BUFFER_SIZE = 1024
FORMAT = "utf-8"
BASE_DIR = Path("./data").resolve()

ADDR = (IP, PORT)

def send_ok(connection: socket, message = ""):
    connection.send(f"OK {message}".encode('utf-8'))

def send_err(connection: socket, message: str):
    connection.send(f"ERR {message}".encode('utf-8'))

def is_valid_path(other_path: Path) -> bool:
    return other_path.is_relative_to(BASE_DIR)

def logon(connection: socket) -> bool:
    data = connection.recv(1024).decode(FORMAT)
    return data == "LOGON"

def handle_upload(connection: socket, params: list[str]):
    
    file_bytes, file_name = int(params[0]), params[1]
    destination = ""

    if len(params) == 3:
        destination = params[2]

    target_file = (BASE_DIR / destination / file_name).resolve()
    
    if not is_valid_path(target_file):
        send_err(connection)
        return
    
    send_ok(connection)

    total_received = 0
    with target_file.open("wb") as file:
        while total_received < file_bytes:
            data = connection.recv(BUFFER_SIZE)
            len_received = len(data)

            total_received += len_received
            file.write(data)
    
    send_ok(connection)


def handle_connection(connection: socket, address):

    print(f"[*] Established connection: {address}")

    if not logon(connection):
        send_err(connection)
        connection.close()
        print(f"[*] Connection closed: {address}")
        return

    send_ok(connection)

    while True:
        data = connection.recv(BUFFER_SIZE).decode("utf-8")

        command = data.split(' ')

        match command[0]:
            case "LOGOFF":
                break
            case "UPLOAD":
                handle_upload(connection, command[1:])

        connection.send(f"---> {data}".encode("utf-8"))

    connection.close()
    print(f"[*] Connection closed: {address}")


def main():

    if not BASE_DIR.is_dir():
        BASE_DIR.mkdir()

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