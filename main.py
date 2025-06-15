import os
import socket
import time
import toml
from multiprocessing import Process


def start_ui(listen_port: int):
    os.system(f"python processes/user_interface.py {listen_port}")


def start_network(listen_port: int):
    os.system(f"python processes/network_communication.py {listen_port}")


def start_discovery():
    os.system("python processes/discovery_service.py")


def check_for_free_port(port_range: str, host: str = "127.0.0.1"):
    start, end = map(int, port_range.split('-'))
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, port))
                return port
            except OSError:
                continue


if __name__ == "__main__":
    CONFIG = toml.load("config.toml")
    LISTEN_PORT_RANGE = CONFIG["general"]["port"]

    free_listen_port = check_for_free_port(LISTEN_PORT_RANGE)

    ui_process = Process(target=start_ui, args=[free_listen_port])
    network_process = Process(target=start_network, args=[free_listen_port])
    discovery_process = Process(target=start_discovery)

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
