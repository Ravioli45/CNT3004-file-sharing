import threading
import socket
from pathlib import Path
from collections import defaultdict

IP = "127.0.0.1" #socket.gethostbyname(socket.gethostname())
PORT = 3300
BUFFER_SIZE = 1024
FORMAT = "utf-8"
BASE_DIR = Path("./data").resolve()
FILE_LOCKS: defaultdict[str, threading.Lock] = defaultdict(lambda : threading.Lock())
SHUTDOWN = False

ADDR = (IP, PORT)

def send_ok(connection: socket.socket, message: str | None = None):
    """sends an OK code across the given connection with the given message"""
    if message is None:
        connection.send("OK".encode('utf-8'))
    else:
        connection.send(f"OK {message}".encode('utf-8'))

def send_err(connection: socket.socket, message: str | None = None):
    """sends an ERR code across the given connection with the given message"""
    if message is None:
        connection.send("ERR".encode('utf-8'))
    else:
        connection.send(f"ERR {message}".encode('utf-8'))

def send_overwrite(connection: socket.socket):
    """sends an OVR code across the diven connection"""
    connection.send("OVR".encode('utf-8'))

def is_valid_path(other_path: Path) -> bool:
    """
    checks the validity of a given path

    returns true if other_path is contained with BASE_DIR
    returns false otherwise
    """
    return other_path.is_relative_to(BASE_DIR)

def logon(connection: socket.socket) -> bool:
    """
    returns true is user has successfully logged on
    returns false otherwise
    """
    data = connection.recv(1024).decode(FORMAT)
    return data == "LOGON"

def handle_upload(connection: socket.socket, params: list[str]):
    """
    function for handling an upload request across a given connection

    params[0] = bytes in the file to be uploaded
    params[1] = file name
    params[2] = optional field indicating directory to upload file to
    """

    file_bytes, file_name = int(params[0]), params[1]
    destination = ""

    if len(params) == 3:
        destination = params[2]

    target_file: Path = (BASE_DIR / destination / file_name).resolve()
    
    if not is_valid_path(target_file) or target_file.is_dir():
        send_err(connection)
        return
    

    if FILE_LOCKS[str(target_file)].acquire(False):

        if target_file.is_file():
            send_overwrite(connection)

            answer = connection.recv(BUFFER_SIZE).decode('utf-8')
            #print(answer)
            if not answer.startswith("OK"):
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
        
        FILE_LOCKS[str(target_file)].release()

        send_ok(connection)
        #print("u done")
    else:
        send_err(connection, "\"File is already being used\"")

def handle_download(connection: socket.socket, params: list[str]):
    """
    function for handling a download request across a given connection

    params[0] = path to file to be downloaded
    """

    file_path = (BASE_DIR / params[0]).resolve()

    if not is_valid_path(file_path) or not file_path.is_file():
        send_err(connection)
        return
    
    if FILE_LOCKS[str(file_path)].acquire(False):

        send_ok(connection, file_path.stat().st_size)

        # awaits OK from client before sending file
        data = connection.recv(1024).decode(FORMAT)

        if not data == "OK":
            send_err(connection)
            return

        with file_path.open('rb') as file:
            connection.sendfile(file)

        # awaits OK from client after receiving file
        data = connection.recv(1024).decode(FORMAT)

        FILE_LOCKS[str(file_path)].release()
        send_ok(connection)

    else:
        send_err(connection, "\"File is already being used\"")


def handle_delete(connection: socket.socket, params: list[str]):
    """
    function for handling a delete request across a given connection

    params[0] = path to file to be deleted
    """
    
    file_path = (BASE_DIR / params[0]).resolve()

    if not is_valid_path(file_path) or not file_path.is_file():
        send_err(connection)
        return
    
    if FILE_LOCKS[str(file_path)].acquire(False):

        file_path.unlink()
        send_ok(connection)

        FILE_LOCKS[str(file_path)].release()

        del FILE_LOCKS[str(file_path)]
    else:
        send_err(connection, "\"Unable to delete file that is being used\"")

def handle_dir(connection: socket.socket, params: list[str]):
    """
    function for handling a dir request across a given connection

    params[0] = optional parameter specifying which directory to print the contents of
    """
    directory = "."

    if len(params) == 1:
        directory = params[0]

    target_directory = (BASE_DIR / directory).resolve()

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

def create_subfolder(connection: socket.socket, target_directory: Path):
    """
    helper function used by handle_subfolder in order to create a new folder at a given path
    """
    try:
        target_directory.mkdir()
        send_ok(connection)
    except Exception:
        send_err(connection, "\"Can't create directory\"")

def delete_subfolder(connection: socket.socket, target_directory: Path):
    """
    helper function used by handle_subfolder in order to delete a new folder at a given path
    """
    if target_directory == BASE_DIR or not target_directory.is_dir():
        send_err(connection)
        return
    
    try:
        target_directory.rmdir()
        send_ok(connection)
    except OSError:
        send_err(connection, "\"Can't delete non-empty folder\"")


def handle_subfolder(connection: socket.socket, params: list[int]):
    """
    function for handling a subfolder request across a given connection

    params[0] = CREATE or DELETE, tells server whether to create or delete a subfolder
    params[1] = the directory to create or delete
    """
    
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
            send_err(connection)



def handle_connection(connection: socket.socket, address):
    """
    general function for handling the connection between server and client during a session

    this function is run on a new thread for every client that connects to the servers
    """
    print(f"[*] Established connection: {address}")

    if not logon(connection):
        send_err(connection)
        connection.close()
        print(f"[*] Connection closed: {address}")
        return

    send_ok(connection)

    connection.settimeout(1.0)

    while True:
        try:
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
                    handle_delete(connection, command[1:])
                case "DIR":
                    handle_dir(connection, command[1:])
                case "SUBFOLDER":
                    handle_subfolder(connection, command[1:])
                case _:
                    pass
        except socket.timeout:
            if SHUTDOWN:
                break


    connection.close()
    print(f"[*] Connection closed: {address}")


def main():
    """
    main fuction

    listens for new connections and creates threads when a user connects to the server
    """
    global SHUTDOWN

    if not BASE_DIR.is_dir():
        BASE_DIR.mkdir()

    print("[*] Starting Server...")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)
    server.listen()

    server.settimeout(1.0)

    print(f"[*] Server is listening on {IP}:{PORT}")

    try:
        while True:
            try:
                (connection, address) = server.accept()

                thread = threading.Thread(target=handle_connection, args=(connection, address))

                thread.start()
            
            except socket.timeout:
                pass
            except KeyboardInterrupt:
                pass

    except KeyboardInterrupt:
        print("[*] Shutting down...")
        SHUTDOWN = True



if __name__ == "__main__":
    main()