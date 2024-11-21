
import os
import socket

from pathlib import Path


IP = "192.168.141.92"
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
    pass
        
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
        
        bytesSent = 0
        while bytesSent < fileBytes:
            bytesSent += SIZE
            client.send(file.read(SIZE))

        data = receiveMsg(client)

        if data.startswith("OK"):
            print(f"[*] Successfully uploaded file: {data}")
        elif data.startswith("ERR"):
            print(f"[!] Server error occurred when uploading file: {data}")


def main():
    client = connect()
    while True:
        data = input("\n> ") 
        data = data.split(" ")
        cmd = data[0]

        if cmd == "LOGOUT":
            logout(client)
            break
        elif cmd == "DOWNLOAD":
            pass
        elif cmd == "UPLOAD":
            if len(data) >= 3:
                upload(client, data[1], data[2])
            else:
                upload(client, data[1], "")


if __name__ == "__main__":
    main()
