

def command_join(handle: str, port: int) -> str:
    return f"JOIN {handle} {port}"


def command_leave(handle: str) -> str:
    return f"LEAVE {handle}"


def command_msg(handle: str, text: str) -> str:
    return f"MSG {handle} {text}"


def command_img(handle: str, size: int) -> str:
    return f"IMG {handle} {size}"


def command_who() -> str:
    return "WHO"


def command_knowusers(users: dict[str, list[str]]) -> str:
    command = "KNOWUSERS"

    for handle, address in users.items():
        ip, port = address
        command += f" {handle} {ip} {port},"
    
    return command
