import socket
import threading
import time


HANDLE = "Client"
BROADCAST_PORT = 4000
LISTEN_PORT = 33333
BUFFER_SIZE = 512
known_users: dict[str, list[str]] = {}


def on_receive(sender: tuple, command: str):
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


def interpret_message(sender: tuple, message: str):
    split_message = message.split(" ", 1)
    command = split_message.pop(0)
    parameters = split_message.pop(0)

    match command:
        case "LEAVE":
            handle = parameters.split(" ")
            on_leave(sender, handle)
        case "MSG":
            handle, text = parameters.split(" ", 1)
            on_msg(sender, handle, text)
        case "IMG":
            handle, size = parameters.split(" ")
            on_img(sender, size)
        case "KNOWUSERS":
            users = parameters.split(",")
            users.pop() # last entry, as it will be empty
            on_knowusers(sender, users)
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
    else:
        if not known_users.get(handle):
            print("[Error] This user is unknown")
            return
        
        ip, port = known_users.get(handle)
        send((ip, port), command_msg(handle, text))


def on_img(sender: tuple, size: int):
    pass


def on_knowusers(sender: tuple, users: list[str]):
    for user in users:
        print(user.split(" "))
        handle, ip, port = user.split(" ")
        known_users.update({handle: [ip, int(port)]})
    
    print(f"Known Users: {known_users}")


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
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(("", LISTEN_PORT))

    print(f"[NetworkCommunication] Listening on UDP port {LISTEN_PORT} for messages...")

    # Execute message listening on another thread to avoid freezing the program
    listening_thread = threading.Thread(target=listen_for_messages, daemon=True)
    listening_thread.start()

    send(("<broadcast>", BROADCAST_PORT), command_join(HANDLE, LISTEN_PORT))
    send(("<broadcast>", BROADCAST_PORT), command_who())

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        send_leave()
        print("[NetworkCommunication] Service stopped")