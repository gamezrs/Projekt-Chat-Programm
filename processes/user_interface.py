import socket


HANDLE = "Client"
BROADCAST_PORT = 4000
LISTEN_PORT = 33333
BUFFER_SIZE = 512


def send(message: str):
    sock.sendto(message.encode(), ("127.0.0.1", LISTEN_PORT))


def send_commands():
    """
    Permanently listening for commands that the user writes
    """
    while True:
        message = input("")
        if len(message) > 512:
            print("[Error] Message too long (max. 512 Symbols)")
            continue
        send(message)



if __name__ == "__main__":
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    send_commands()