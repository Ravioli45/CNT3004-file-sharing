
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
    pass


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
            pass


if __name__ == "__main__":
    main()
