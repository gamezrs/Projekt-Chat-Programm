import socket
import threading
import time
from ..protocol import *


HANDLE = "Client"
BROADCAST_PORT = 4000
LISTEN_PORT = 33333
BUFFER_SIZE = 512


def on_receive(sender: socket._Address, command: str):
    print(f"[NetworkCommunication] New message {sender}: {command}")
    interpret_message(sender, command)


def send(receiver, command: str):
    sock.sendto(command.encode(), receiver)
    print(f"[NetworkCommunication] Sent to {receiver}: {command}")


def listen_for_messages():
    """
    Permanently listening for messages
    """
    while True:
        data, sender = sock.recvfrom(BUFFER_SIZE)
        message = data.decode()
        on_receive(sender, message)


def interpret_message(sender: socket._Address, message: str):
    split_message = message.split(" ", 1)
    command = split_message.pop(0)
    parameters = split_message.pop(0)

    match command:
        case "MSG":
            handle, text = parameters.split(" ")
            on_msg(sender, text)
        case "IMG":
            handle, size = parameters.split(" ")
            on_img(sender, size)
        case _:
            print(f"[Error] Command {command} does not exist")


def on_msg(sender: socket._Address, text: str):
    pass


def on_img(sender: socket._Address, size: int):
    pass


if __name__ == "__main__":
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(LISTEN_PORT)

    print(f"[NetworkCommunication] Listening on UDP port {LISTEN_PORT} for messages...")

    # Execute message listening on another thread to avoid freezing the program
    listening_thread = threading.Thread(target=listen_for_messages, daemon=True)
    listening_thread.start()

    send(("<broadcast>", BROADCAST_PORT), command_join(HANDLE, LISTEN_PORT))

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        send(("<broadcast>", BROADCAST_PORT), command_leave(HANDLE))
        print("[NetworkCommunication] Service stopped")