import socket
import sys
import toml


CONFIG = toml.load("config.toml")
HANDLE = CONFIG["general"]["handle"]
BROADCAST_PORT = CONFIG["general"]["whoisport"]
AUTO_REPLY = CONFIG["general"]["autoreply"]
BUFFER_SIZE = 1024


def send(message: str):
    global listen_port

    split_message = message.split(" ", 1)
    command = split_message.pop(0)
    if len(split_message) > 0:
        parameters = split_message.pop(0)
    
    command_to_send = ""

    match command:
        case "msg":
            command_to_send = f"MSG {parameters}"
            sock.sendto(command_to_send.encode(), ("127.0.0.1", listen_port))
        case "img":
            handle, file_path = parameters.split(" ", 1)
            command_to_send = f"IMGREQUEST {handle} {file_path}"
            sock.sendto(command_to_send.encode(), ("127.0.0.1", listen_port))
        case "config":
            key, value = parameters.split(" ", 1)
            CONFIG["general"][key] = value
            with open("config.toml", "w") as file:
                toml.dump(CONFIG, file)
            print("Config updated!")
        case "afk":
            sock.sendto(f"AFK".encode(), ("127.0.0.1", listen_port))


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
    listen_port = int(sys.argv[1])
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    send_commands()