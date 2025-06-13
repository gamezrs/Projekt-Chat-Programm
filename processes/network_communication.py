import socket
import threading
import time


LISTEN_PORT = 33333
BUFFER_SIZE = 512


def on_receive(sender, command: str):
    print(f"[NetworkCommunication] New message {sender}: {command}")


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



if __name__ == "__main__":
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(LISTEN_PORT)

    print(f"[NetworkCommunication] Listening on UDP port {LISTEN_PORT} messages...")

    # Execute message listening on another thread to avoid freezing the program
    listening_thread = threading.Thread(target=listen_for_messages, daemon=True)
    listening_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[NetworkCommunication] Service stopped")