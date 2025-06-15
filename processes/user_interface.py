import socket


HANDLE = "Client"
BROADCAST_PORT = 4000
LISTEN_PORT = 33333
BUFFER_SIZE = 1024
CHUNK_SIZE = 512


def send(message: str):
    split_message = message.split(" ", 1)
    command = split_message.pop(0)
    if len(split_message) > 0:
        parameters = split_message.pop(0)
    
    command_to_send = ""

    match command:
        case "msg":
            command_to_send = f"MSG {parameters}"
            sock.sendto(command_to_send.encode(), ("127.0.0.1", LISTEN_PORT))
        case "img":
            handle, file_path = parameters.split(" ", 1)
            command_to_send = f"IMGREQUEST {handle} {file_path}"
            sock.sendto(command_to_send.encode(), ("127.0.0.1", LISTEN_PORT))


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