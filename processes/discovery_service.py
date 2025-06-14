import socket
import threading
import time


BROADCAST_PORT = 4000
BUFFER_SIZE = 512


def on_receive(sender):
    print(f"[DiscoveryService] Discovered {sender}")


def listen_for_messages():
    """
    Permanently listening for messages
    """
    while True:
        data, sender = sock.recvfrom(BUFFER_SIZE)
        on_receive(sender)



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
