import os
import socket
import sys
import threading
import time
import toml


CONFIG = toml.load("config.toml")
HANDLE = CONFIG["general"]["handle"]
BROADCAST_PORT = CONFIG["general"]["whoisport"]
BUFFER_SIZE = 1024
known_users: dict[str, list[str]] = {}


def on_receive(sender: tuple, message: str):
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


def interpret_discovery_message(sender: tuple, message: str):
    split_message = message.split(" ", 1)
    command = split_message.pop(0)
    if len(split_message) > 0:
        parameters = split_message.pop(0)

    match command:
        case "JOIN":
            handle, port = parameters.split(" ")
            on_join(sender, handle, port)
        case "LEAVE":
            (handle,) = parameters.split(" ")
            on_leave(sender, handle)
        case "WHO":
            on_who(sender)
        case _:
            print(f"[Error] Command {command} does not exist")


def on_join(sender: tuple, handle: str, port: int):
    known_users.update({handle: [sender[0], port]})
    
    if handle != HANDLE:
        send(("127.0.0.1", listen_port), command_knowusers(known_users))


def on_leave(sender: tuple, handle: str):
    if not known_users.get(handle):
        return
    known_users.pop(handle)


def on_who(sender: tuple):
    send(sender, command_knowusers(known_users))


def command_knowusers(users: dict[str, list[str]]) -> str:
    command = "KNOWUSERS"

    for handle, address in users.items():
        ip, port = address
        command += f" {handle} {ip} {port},"
    
    return command


if __name__ == "__main__":
    listen_port = int(sys.argv[1])
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(("", BROADCAST_PORT))

    print(f"[DiscoveryService] Listening on UDP port {BROADCAST_PORT} for discoveries...")

    # Execute message listening on another thread to avoid freezing the program
    listening_thread = threading.Thread(target=listen_for_messages, daemon=True)
    listening_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        os.remove("./discovery.lock")
        print("[DiscoveryService] Service stopped")
