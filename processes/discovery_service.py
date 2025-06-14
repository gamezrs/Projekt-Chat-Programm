import socket
import threading
import time
from ..protocol import *


HANDLE = "Client"
BROADCAST_PORT = 4000
LISTEN_PORT = 33333
BUFFER_SIZE = 512


def on_receive(sender: socket._Address, message: str):
    print(f"[DiscoveryService] Discovered {sender}")
    interpret_discovery_message(sender, message)


def send(receiver, command: str):
    sock.sendto(command.encode(), receiver)
    print(f"[DiscoveryService] Sent to {receiver}: {command}")


def listen_for_messages():
    """
    Permanently listening for messages
    """
    while True:
        data, sender = sock.recvfrom(BUFFER_SIZE)
        message = data.decode()
        on_receive(sender, message)


def interpret_discovery_message(sender: socket._Address, message: str):
    split_message = message.split(" ", 1)
    command = split_message.pop(0)
    parameters = split_message.pop(0)

    match command:
        case "JOIN":
            handle, port = parameters.split(" ")
            on_join(sender, handle, port)
        case "LEAVE":
            handle = parameters.split(" ")
            on_leave(sender, handle)
        case "WHO":
            on_who(sender)
        case "KNOWUSERS":
            on_knowusers(sender)
        case _:
            print(f"[Error] Command {command} does not exist")


def on_join(sender: socket._Address, handle: str, port: int):
    pass


def on_leave(sender: socket._Address, handle: str):
    pass


def on_who(sender: socket._Address):
    pass


def on_knowusers(sender: socket._Address):
    pass


if __name__ == "__main__":
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(BROADCAST_PORT)

    print(f"[DiscoveryService] Listening on UDP port {BROADCAST_PORT} for discoveries...")

    # Execute message listening on another thread to avoid freezing the program
    listening_thread = threading.Thread(target=listen_for_messages, daemon=True)
    listening_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[DiscoveryService] Service stopped")
