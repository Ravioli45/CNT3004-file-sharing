import threading
import socket
from pathlib import Path

IP = "127.0.0.1" #socket.gethostbyname(socket.gethostname())
PORT = 3300
BUFFER_SIZE = 1024
FORMAT = "utf-8"
BASE_DIR = Path("./data").resolve()

ADDR = (IP, PORT)

def send_ok(connection: socket, message: str | None = None):
    if message is None:
        connection.send("OK".encode('utf-8'))
    else:
        connection.send(f"OK {message}".encode('utf-8'))

def send_err(connection: socket, message: str | None = None):
    if message is None:
        connection.send("ERR".encode('utf-8'))
    else:
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
    
    if not is_valid_path(target_file) or target_file.is_dir():
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

def handle_download(connection: socket, params: list[str]):
    
    file_path = (BASE_DIR / params[0]).resolve()

    if not is_valid_path(file_path) or not file_path.is_file():
        send_err(connection)
        return
    
    # send OK (file size in bytes)
    send_ok(connection, file_path.stat().st_size)

    # awaits OK from client before sending file
    data = connection.recv(1024).decode(FORMAT)

    if not data == "OK":
        send_err(connection)
        return

    with file_path.open('rb') as file:
        connection.sendfile(file)
    
    send_ok(connection)

def handle_delete():
    pass

def handle_dir(connection: socket, params: list[str]):
    directory = "."

    if len(params) == 1:
        directory = params[0]

    target_directory = (BASE_DIR / directory).resolve()
    #print(target_directory)
    #print(target_directory.relative_to(BASE_DIR))

    if not is_valid_path(target_directory) or not target_directory.is_dir():
        send_err(connection)
        return
    

    directory_info = "\""

    for object in target_directory.iterdir():
        if object.is_dir():
            directory_info += f"directory {object.relative_to(BASE_DIR)}\n"
        else:
            directory_info += f"file {object.relative_to(BASE_DIR)}\n"
    directory_info += "\""

    send_ok(connection, directory_info)

def create_subfolder(connection: socket, target_directory: Path):

    try:
        target_directory.mkdir()
        send_ok(connection)
    except Exception:
        send_err(connection, "\"Can't create directory\"")

def delete_subfolder(connection: socket, target_directory: Path):

    if target_directory == BASE_DIR or not target_directory.is_dir():
        send_err(connection)
        return
    
    try:
        target_directory.rmdir()
        send_ok(connection)
    except OSError:
        send_err(connection, "\"Can't delete non-empty folder\"")


def handle_subfolder(connection: socket, params: list[int]):
    
    # should be CREATE or DELETE
    action = params[0]

    directory = params[1]

    target_directory = (BASE_DIR / directory).resolve()

    if not is_valid_path(target_directory) or target_directory.is_file():
        send_err(connection)
        return
    
    match action:
        case "CREATE":
            create_subfolder(connection, target_directory)
        case "DELETE":
            delete_subfolder(connection, target_directory)
        case _:
            pass



def handle_connection(connection: socket, address):

    print(f"[*] Established connection: {address}")

    if not logon(connection):
        send_err(connection)
        connection.close()
        print(f"[*] Connection closed: {address}")
        return

    send_ok(connection)

    while True:
        data = connection.recv(BUFFER_SIZE).decode(FORMAT)

        command = data.split(' ')

        match command[0]:
            case "LOGOFF":
                break
            case "UPLOAD":
                handle_upload(connection, command[1:])
            case "DOWNLOAD":
                handle_download(connection, command[1:])
            case "DELETE":
                pass
            case "DIR":
                handle_dir(connection, command[1:])
            case "SUBFOLDER":
                handle_subfolder(connection, command[1:])
            case _:
                pass


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