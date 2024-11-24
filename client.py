
import os
import socket

from pathlib import Path


IP = "127.0.0.1"
PORT = 3300
ADDR = (IP, PORT)

SIZE = 1024
FORMAT = "utf-8"

def sendMsg(client: socket, message: str):
    client.send(message.encode(FORMAT))

def receiveMsg(client: socket):
    return client.recv(SIZE).decode(FORMAT)

def connect() -> socket:
    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    client.connect(ADDR)

    print("[*] Logging into server...")
    sendMsg(client, "LOGON")

    data = receiveMsg(client)
    if data.startswith("OK"):
        return client
    else:
        raise Exception("[!] Could not log into the server.")


def logout(client: socket):
    print("[*] Logging out...")
    sendMsg(client, "LOGOUT")

# Download from server's srcPath to client's destPath
def download(client: socket, srcPath: str, destPath: str):
    
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
            file.write(client.recv(SIZE))
            received += SIZE

        print("[*] File downloaded, awaiting confirmation from server...")
        sendMsg(client, "OK")

        res = receiveMsg(client)
        if res.startswith("OK"):
            print(f"[*] File successfully downloaded from server: {res}")
        elif res.startswith("ERR"):
            print(f"[!] Server encountered error when downloading: {res}")
        
def upload(client: socket, srcPath: str, destPath: str):
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
            c = 0
            while c != 'y' and c != 'n':
                c = input(f"[?] This file already exists on the server. Do you want to overwrite it? (y/n): ").strip()
            
            if c == 'n':
                sendMsg(client, "ERR: client does not want to overwite file")
                print("[*] Permission to overwrite file denied.")
                return
            else:
                sendMsg(client, "OK: overwrite file")
                print("[*] Permission to overwrite file granted.")
        
        bytesSent = 0
        while bytesSent < fileBytes:
            bytesSent += SIZE
            client.send(file.read(SIZE))

        data = receiveMsg(client)

        if data.startswith("OK"):
            print(f"[*] Successfully uploaded file: {data}")
        elif data.startswith("ERR"):
            print(f"[!] Server error occurred when uploading file: {data}")

def handle_delete(client: socket, path: str):
    sendMsg(client, f"DELETE {path}")

    data = receiveMsg(client)

    if not data.startswith("OK"):
        print(f"[!] Server encountered error when deleting file: {data}")
        return
    else:
        print("[*] File successfully deleted.")

def handle_subfolder_create(client: socket, path: str):
    sendMsg(client, f"SUBFOLDER CREATE {path}")

    data = receiveMsg(client)

    if not data.startswith("OK"):
        print(f"[!] Server encountered error when creating subfolder: {data}")
    else:
        print("[*] Subfolder successfully created.")

def handle_subfolder_delete(client: socket, path: str):
    sendMsg(client, f"SUBFOLDER DELETE {path}")

    data = receiveMsg(client)

    if not data.startswith("OK"):
        print(f"[!] Server encountered error when deleting subfolder: {data}")
    else:
        print("[*] Subfolder successfully deleted.")

def main():
    client = connect()
    while True:
        data = input("\n> ").strip()
        data = data.split(" ")
        cmd = data[0].lower()

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


if __name__ == "__main__":
    main()
