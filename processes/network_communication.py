import os
import socket
import sys
import threading
import time
import toml


CONFIG = toml.load("config.toml")
HANDLE = CONFIG["general"]["handle"]
BROADCAST_PORT = CONFIG["general"]["whoisport"]
AUTO_REPLY = CONFIG["general"]["autoreply"]
IMAGE_PATH = CONFIG["general"]["imagepath"]
BUFFER_SIZE = 1024
afk = False
known_users: dict[str, list[str]] = {}
image_buffer_size = BUFFER_SIZE


def on_receive(sender: tuple, command: str):
    print(f"[NetworkCommunication] New message {sender}: {command}")
    interpret_message(sender, command)


def send(receiver, command: str | bytes, protocol: str = "UDP"):
    if isinstance(command, str):
        command = command.encode()
    
    if protocol == "UDP":
        sock.sendto(command, receiver)
    elif protocol == "TCP":
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcpsock:
            tcpsock.connect(receiver)
            tcpsock.sendall(command)

    print(f"[NetworkCommunication] Sent to {receiver}: {command}")


def listen_for_messages():
    """
    Permanently listening for UDP messages and interprets messages as commands
    """
    while True:
        data, sender = sock.recvfrom(BUFFER_SIZE)
        message = data.decode()
        on_receive(sender, message)


def listen_for_tcp_messages():
    """
    Permanently listening for TCP messages and interprets messages as commands
    """
    tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server.bind(("", listen_port))
    tcp_server.listen()

    print(f"[NetworkCommunication] Listening on TCP port {listen_port} for messages...")

    while True:
        conn, addr = tcp_server.accept()
        with conn:
            data = conn.recv(image_buffer_size)
            if not data:
                continue
            try:
                message = data.decode()
                on_receive(addr, message)
            except UnicodeDecodeError:
                on_img_binary(addr, data)


def interpret_message(sender: tuple, message: str):
    """
    Interprets the messages as commands and calls their respective functions
    """
    split_message = message.split(" ", 1)
    command = split_message.pop(0)
    if len(split_message) > 0:
        parameters = split_message.pop(0)

    match command:
        case "LEAVE":
            parameters = parameters.split(" ", 1)
            if not len(parameters) > 0: return
            (handle,) = parameters
            on_leave(sender, handle)
        case "MSG":
            parameters = parameters.split(" ", 1)
            if not len(parameters) > 1: return
            handle, text = parameters
            on_msg(sender, handle, text)
        case "IMG":
            parameters = parameters.split(" ")
            if not len(parameters) > 1: return
            handle, size = parameters
            on_img(sender, handle, int(size))
        case "IMGREQUEST":
            parameters = parameters.split(" ")
            if not len(parameters) > 1: return
            handle, file_path = parameters
            on_imgrequest(sender, handle, file_path)
        case "KNOWUSERS":
            users = parameters.split(",")
            users.pop() # last entry, as it will be empty
            on_knowusers(sender, users)
        case "AFK":
            global afk
            if not afk:
                print(f"[AFK] You are now AFK, The program will autoreply \"{AUTO_REPLY}\"")
                afk = True
            else:
                print("[AFK] You are no longer AFK")
                afk = False

        case _:
            print(f"[Error] Command {command} does not exist")


def on_leave(sender: tuple, handle: str):
    """
    Removes the user that left from the known users dictionary and prints a message with currently online users
    """
    if not known_users.get(handle):
        return
    known_users.pop(handle)
    
    print(f"{handle} has left the chat")
    print(f"Online users: {" ".join(known_users.keys())}")


def on_msg(sender: tuple, handle: str, text: str):
    """
    When a message is received that is addressed to the handle of this client, it is simply print
    and in case the user has set the AFK flag, an autoreply is sent back.

    If a message reaches this client that is not addressed to it, the message came from the user interface
    and the client sends a message to the addressed client.
    """
    if handle == HANDLE:
        name = get_handle_from_sender(sender)
        text = text.removeprefix("\"").removesuffix("\"")
        print(f"{name}: {text}")

        global afk
        if afk:
            print(f"{HANDLE}: {AUTO_REPLY}")
            send(sender, f"MSG {name} {AUTO_REPLY}", "TCP")
    else:
        if not known_users.get(handle):
            print("[Error] This user is unknown")
            return
        
        ip, port = known_users.get(handle)
        send((ip, port), command_msg(handle, text), "TCP")


def on_img(sender: tuple, handle: str, size: int):
    """
    Sets the flags so that the client knows, the next message is an image
    """
    global image_buffer_size
    image_buffer_size = size


def on_imgrequest(sender: tuple, handle: str, file_path: str):
    """
    Sends an image to another client when the user interface requests it
    """
    if not known_users.get(handle):
        print("[Error] This user is unknown")
        return
    
    if not os.path.exists(file_path):
        print("[Error] File does not exist")
        return
    
    with open(file_path, "rb") as file:
        content = file.read()
        size = len(content)
        
    ip, port = known_users.get(handle)
    send((ip, port), command_img(handle, size), "TCP")
    send((ip, port), content, "TCP")


def on_img_binary(sender: tuple, content: bytes):
    """
    Receives the image content in binary, saves it to disk and opens it
    """
    global image_buffer_size
    image_buffer_size = BUFFER_SIZE

    file_name = f"{IMAGE_PATH}/{time.time_ns()}.png"

    with open(file_name, "xb") as file:
        file.write(content)
    
    os.startfile(file_name)

    print(f"You received an image from {get_handle_from_sender(sender)}")


def on_knowusers(sender: tuple, users: list[str]):
    """
    Updates the known users dictionary and prints a message with currently online users
    """
    online_users = ""
    for user in users:
        handle, ip, port = user.removeprefix(" ").split(" ")
        known_users.update({handle: [ip, int(port)]})
        online_users += f" {handle}"
    
    print(f"New user joined the chat")
    print(f"Online users:{online_users}")


def command_join(handle: str, port: int) -> str:
    return f"JOIN {handle} {port}"


def command_leave(handle: str) -> str:
    return f"LEAVE {handle}"


def command_msg(handle: str, text: str) -> str:
    return f"MSG {handle} \"{text}\""


def command_img(handle: str, size: int) -> str:
    return f"IMG {handle} {size}"


def command_who() -> str:
    return "WHO"


def get_handle_from_sender(sender: tuple) -> str:
    """
    Returns the handle of the sender if it is found in the known users dictionary
    and matches the saved users ip and port
    """
    for handle, address in known_users.items():
        sender_ip, sender_port = sender
        user_ip, user_port = address
        if sender_ip == user_ip and sender_port == user_port:
            return handle
    return "Unknown"


def send_leave():
    """
    Sends a LEAVE broadcast to all discovery servers and a unicast to all known users
    """
    send(("<broadcast>", BROADCAST_PORT), command_leave(HANDLE))
    for handle, address in known_users.items():
        ip, port = address
        send((ip, port), command_leave(HANDLE))


if __name__ == "__main__":
    listen_port = int(sys.argv[1])

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(("", listen_port))

    print(f"[NetworkCommunication] Listening on UDP port {listen_port} for messages...")

    # Execute message listening on another thread to avoid freezing the program
    listening_thread = threading.Thread(target=listen_for_messages, daemon=True)
    listening_thread.start()

    tcp_listening_thread = threading.Thread(target=listen_for_tcp_messages, daemon=True)
    tcp_listening_thread.start()

    send(("<broadcast>", BROADCAST_PORT), command_join(HANDLE, listen_port))
    send(("<broadcast>", BROADCAST_PORT), command_who())

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        send_leave()
        print("[NetworkCommunication] Service stopped")