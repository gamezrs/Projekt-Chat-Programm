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
next_message_is_image = False
image_buffer_size = 0


def on_receive(sender: tuple, command: str):
    print(f"[NetworkCommunication] New message {sender}: {command}")
    interpret_message(sender, command)


def send(receiver, command: str | bytes):
    if isinstance(command, str):
        command = command.encode()

    sock.sendto(command, receiver)
    print(f"[NetworkCommunication] Sent to {receiver}: {command}")


def listen_for_messages():
    """
    Permanently listening for messages
    """
    while True:
        global next_message_is_image

        if not next_message_is_image:
            data, sender = sock.recvfrom(BUFFER_SIZE)
            message = data.decode()
            on_receive(sender, message)
        else:
            global image_buffer_size
            data, sender = sock.recvfrom(image_buffer_size)
            on_img_binary(sender, data)


def interpret_message(sender: tuple, message: str):
    split_message = message.split(" ", 1)
    command = split_message.pop(0)
    if len(split_message) > 0:
        parameters = split_message.pop(0)

    match command:
        case "LEAVE":
            parameters = parameters.split(" ", 1)
            if not len(parameters) > 0: return
            handle = parameters
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
    if not known_users.get(handle):
        return
    known_users.pop(handle)


def on_msg(sender: tuple, handle: str, text: str):
    if handle == HANDLE:
        name = get_handle_from_sender(sender)
        text = text.removeprefix("\"").removesuffix("\"")
        print(f"{name}: {text}")

        global afk
        if afk:
            print(f"{HANDLE}: {AUTO_REPLY}")
            send(sender, f"MSG {handle} {AUTO_REPLY}")
    else:
        if not known_users.get(handle):
            print("[Error] This user is unknown")
            return
        
        ip, port = known_users.get(handle)
        send((ip, port), command_msg(handle, text))


def on_img(sender: tuple, handle: str, size: int):
    global next_message_is_image
    next_message_is_image = True

    global image_buffer_size
    image_buffer_size = size


def on_imgrequest(sender: tuple, handle: str, file_path: str):
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
    send((ip, port), command_img(handle, size))
    send((ip, port), content)


def on_img_binary(sender: tuple, content: bytes):
    global next_message_is_image
    next_message_is_image = False

    global image_buffer_size
    image_buffer_size = 0

    file_name = f"{IMAGE_PATH}/{time.time_ns()}.png"

    with open(file_name, "xb") as file:
        file.write(content)
    
    os.startfile(file_name)


def on_knowusers(sender: tuple, users: list[str]):
    for user in users:
        handle, ip, port = user.split(" ")
        known_users.update({handle: [ip, int(port)]})


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
    for handle, address in known_users.items():
        sender_ip, sender_port = sender
        user_ip, user_port = address
        if sender_ip == user_ip and sender_port == user_port:
            return handle
    return "Unknown"


def send_leave():
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

    send(("<broadcast>", BROADCAST_PORT), command_join(HANDLE, listen_port))
    send(("<broadcast>", BROADCAST_PORT), command_who())

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        send_leave()
        print("[NetworkCommunication] Service stopped")