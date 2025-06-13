import os
from multiprocessing import Process


def start_ui():
    os.system("python processes/user_interface.py")


def start_network():
    os.system("python processes/network_communication.py")


def start_discovery():
    os.system("python processes/discovery_service.py")



if __name__ == "__main__":
    ui_process = Process(target=start_ui)
    network_process = Process(target=start_network)
    discovery_process = Process(target=start_discovery)

    ui_process.start()
    network_process.start()
    if not os.path.exists("./discovery.lock"):
        with open("./discovery.lock", "w") as file:
            file.write("running")
        discovery_process.start()

    ui_process.join()
    network_process.join()
    if discovery_process.is_alive():
        discovery_process.join()
