"""Returns a http server object with wiznet compatible socket and an IP to listen on"""

import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket

from adafruit_httpserver import Server

from wiznet5keth import NetworkConfig, config_eth
from config_utils import get_config_from_json_file


def get_server(config_file_path: str, static_file_path: str = "/static", debug: bool = True) -> tuple:
    """Returns a server object and IP"""
    eth_config = config_eth(NetworkConfig(**get_config_from_json_file(config_file_path)))
    socket.set_interface(eth_config)
    server = Server(socket, static_file_path, debug=debug)
    return server, str(eth_config.pretty_ip(eth_config.ip_address))
