
import os
import socket

from pathlib import Path


IP = "127.0.0.1"
PORT = 3300

SIZE = 1024
FORMAT = "utf-8"

def sendMsg(client: socket, message: str):
    """
    function that sends a text message from the client to the server.
    """
    client.send(message.encode(FORMAT))

def receiveMsg(client: socket):
    """
    function that receives and decodes a text message from the server to the client.

    returns the decoded text message from the server.
    """
    return client.recv(SIZE).decode(FORMAT)

def connect(ip: str) -> socket:
    """
    function that connects to the server using a socket.

    returns the connected socket on success, and otherwise raises an exception.
    """
    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    client.connect((ip, PORT))

    print("[*] Logging into server...")
    sendMsg(client, "LOGON")

    data = receiveMsg(client)
    if data.startswith("OK"):
        return client
    else:
        raise Exception("[!] Could not log into the server.")


def logout(client: socket):
    """
    disconnects the client from the server
    """
    print("[*] Logging out...")
    sendMsg(client, "LOGOUT")

# Download from server's srcPath to client's destPath
def download(client: socket, srcPath: str, destPath: str):
    """
    function that requests the server to download a file from its srcPath to the client's destPath.

    srcPath is based on the server's directory structure, and destPath is based on the client's
    directory structure. Handles overwriting and errors.
    """
    # User might have omitted the file name from the destination path. If so, add it.
    fileName = Path(srcPath).name
    if not destPath.endswith(fileName):
        destPath = str(Path(destPath) / fileName)

    # Ensure user wants to overwrite an existing file
    if os.path.isfile(destPath):
        c = 0
        while c != "y" and c != "n":
            c = input("[?] A file already exists at this location. Overwrite it? (y/n): ")

        if c == "n":
            return
        
    sendMsg(client, f"DOWNLOAD {srcPath}")
    data = receiveMsg(client)

    if data.startswith("ERR"):
        print(f"[*] Server encountered an error when locating file: {data}")
        return

    fileBytes = int(data.split(" ")[1])
    print(f"[*] Preparing to receive {fileBytes} bytes from server.")

    with open(destPath, "wb") as file:

        sendMsg(client, "OK")
        received = 0
        while received < fileBytes:
            recData = client.recv(SIZE)
            file.write(recData)
            received += len(recData)

        print("[*] File downloaded, awaiting confirmation from server...")
        sendMsg(client, "OK")

        res = receiveMsg(client)
        if res.startswith("OK"):
            print(f"[*] File successfully downloaded from server: {res}")
        elif res.startswith("ERR"):
            print(f"[!] Server encountered error when downloading: {res}")
        
def upload(client: socket, srcPath: str, destPath: str):
    """
    Uploads a file from the client's srcPath to the server's destPath. Both paths must be valid
    on their side.
    """
    if not os.path.isfile(srcPath):
        print("[!] Could not find file to upload.")
        return
    
    fileBytes = os.path.getsize(srcPath)

    with open(srcPath, "rb") as file:
        print(f"[*] Preparing {fileBytes} bytes to send to the server")

        sendMsg(client, f"UPLOAD {fileBytes} {srcPath} {destPath}")

        data = receiveMsg(client)

        if data.startswith("ERR"):
            print(f"[!] Server encountered an error: {data}")
            return
        elif data.startswith("OVR"):
            # Determine if user wants to overwrite the file on the server or not.
            c = 0
            while c != 'y' and c != 'n':
                c = input(f"[?] This file already exists on the server. Do you want to overwrite it? (y/n): ").strip()
            
            if c == 'n':
                sendMsg(client, "ERR: client does not want to overwite file")
                print("[*] Permission to overwrite file denied.")
                receiveMsg(client)
                return
            else:
                sendMsg(client, "OK: overwrite file")
                print("[*] Permission to overwrite file granted.")
                receiveMsg(client)

        client.sendfile(file)

        data = receiveMsg(client)

        if data.startswith("OK"):
            print(f"[*] Successfully uploaded file: {data}")
        elif data.startswith("ERR"):
            print(f"[!] Server error occurred when uploading file: {data}")

def handle_delete(client: socket, path: str):
    """
    function that requests a file on the server to be deleted.

    path refers to a valid path on the server-side.
    """
    sendMsg(client, f"DELETE {path}")

    data = receiveMsg(client)

    if not data.startswith("OK"):
        print(f"[!] Server encountered error when deleting file: {data}")
        return
    else:
        print("[*] File successfully deleted.")

def handle_subfolder_create(client: socket, path: str):
    """
    function that requests a new folder based on the given path.
    """
    sendMsg(client, f"SUBFOLDER CREATE {path}")

    data = receiveMsg(client)

    if not data.startswith("OK"):
        print(f"[!] Server encountered error when creating subfolder: {data}")
    else:
        print("[*] Subfolder successfully created.")

def handle_subfolder_delete(client: socket, path: str):
    """
    function that requests deleting an empty subfolder based on the given path.
    """
    sendMsg(client, f"SUBFOLDER DELETE {path}")

    data = receiveMsg(client)

    if not data.startswith("OK"):
        print(f"[!] Server encountered error when deleting subfolder: {data}")
    else:
        print("[*] Subfolder successfully deleted.")

def handle_dir(client: socket, path: str):
    """
    function that displays all of the files and directories under the given path on the server.
    """
    sendMsg(client, f"DIR {path}")

    data = receiveMsg(client)
    if not data.startswith("OK"):
        print(f"[!] Server encountered error when showing directory: {data}")
    else:
        print(f"[*] Listing all folders and files under {path}\n")
        print(" ".join(data.split(" ")[1:])[1:-1])


def main():
    """
    handles interpreting the input from the terminal. Also performs the necessary set-up and
    connection to the server.
    """
    ip = input("[?] Insert the IP address of the server\n> ")
    client = connect(ip)
    while True:
        data = input("\n> ").strip()
        data = data.split(" ")
        cmd = data[0].lower()

        # Funnel user inputs into correct function based on command
        if cmd == "logout":
            logout(client)
            break
        elif cmd == "download":
            if len(data) >= 3:
                download(client, data[1], data[2])
            else:
                download(client, data[1], "./")
        elif cmd == "upload":
            if len(data) >= 3:
                upload(client, data[1], data[2])
            else:
                upload(client, data[1], "")
        elif cmd == "delete":
            handle_delete(client, data[1])
        elif cmd == "subfolder":
            if data[1] == "create":
                handle_subfolder_create(client, data[2])
            elif data[1] == "delete":
                handle_subfolder_delete(client, data[2])
        elif cmd == "dir":
            if len(data) >= 2:
                handle_dir(client, data[1])
            else:
                handle_dir(client, "./")


if __name__ == "__main__":
    main()
