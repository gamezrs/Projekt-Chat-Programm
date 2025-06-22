import os
import socket
import time
import toml
from multiprocessing import Process


def start_ui(listen_port: int):
    os.system(f"python processes/user_interface.py {listen_port}")


def start_network(listen_port: int):
    os.system(f"python processes/network_communication.py {listen_port}")


def start_discovery(listen_port: int):
    os.system(f"python processes/discovery_service.py {listen_port}")


def check_for_free_port(port_range: str, host: str = "127.0.0.1") -> int:
    """
    Checks for a free port where both a TCP and UDP socket can bind on the same host.
    Returns the first available port that works for both protocols.
    """
    start, end = map(int, port_range.split('-'))
    for port in range(start, end):
        try:
            udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_sock.bind((host, port))

            tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_sock.bind((host, port))

            udp_sock.close()
            tcp_sock.close()
            return port

        except OSError:
            udp_sock.close()
            if 'tcp_sock' in locals():
                tcp_sock.close()
            continue


if __name__ == "__main__":
    CONFIG = toml.load("config.toml")
    LISTEN_PORT_RANGE = CONFIG["general"]["port"]

    free_listen_port = check_for_free_port(LISTEN_PORT_RANGE)

    ui_process = Process(target=start_ui, args=[free_listen_port])
    network_process = Process(target=start_network, args=[free_listen_port])
    discovery_process = Process(target=start_discovery, args=[free_listen_port])

    if not os.path.exists("./discovery.lock"):
        with open("./discovery.lock", "w") as file:
            file.write("running")
        discovery_process.start()
        time.sleep(1)
    network_process.start()
    time.sleep(1)
    ui_process.start()

    if discovery_process.is_alive():
        discovery_process.join()
    network_process.join()
    ui_process.join()
