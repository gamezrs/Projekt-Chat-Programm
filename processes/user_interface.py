from ..protocol import interpret_command


def send_commands():
    """
    Permanently listening for commands that the user writes
    """
    while True:
        command = input("> ")
        if len(command) > 512:
            print("[Error] Message too long (max. 512 Symbols)")
            continue
        interpret_command(command)



if __name__ == "__main__":
    send_commands()