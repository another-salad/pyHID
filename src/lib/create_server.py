"""Creates a server object for the pyHID web app."""

def _wiznet5k(*args, **kwargs) -> tuple:
    """Returns a wiznet5k server object and an ip to listen on"""
    from wiznet5k_server import get_server
    return get_server(*args, **kwargs)

SUPPORTED_DEVICES = {
    "wiznet5k":  _wiznet5k # Bucket for Wiznet5k Pico boards (W5100S, W5500)
}

def get_server_and_ip(board: str, *args, **kwargs):
    """Returns a server object and an ip to listen on"""
    if board not in SUPPORTED_DEVICES:
        raise NotImplementedError(f"Board {board} is not supported.")
    return SUPPORTED_DEVICES[board](*args, **kwargs)
