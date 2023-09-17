"""
    requirements:
      - adafruit_http_server (submoduled in for Wiznet W5xxxx board support, README for more details)
      - adafruit_hid
      - adafruit_wiznet5k (required by submodule circuit-python-utils)
      - adafuit_bus_device (required in by submodule circuit-python-utils)
      - circuit-python-utils (submodule)
          - wiznet5keth.py
          - wsgi_web_app_helpers.py
      - All files from 'lib' directory
"""

from adafruit_httpserver import Request, JSONResponse, GET, POST

# Keyboard Layouts
from supported_keyboards import SUPPORTED_KEYBOARDS

# circuit-python-utils
from config_utils import get_config_from_json_file

# usb_hid_helpers
from usb_hid_helpers import type_chars, type_keycodes, json_resp
# HTTP server
from create_server import get_server_and_ip

# config files
PYHID_CONFIG = get_config_from_json_file("config/pyhid_config.json")
API_ENDPOINTS = PYHID_CONFIG["api_endpoints"]

# Configure server
server, listening_ip = get_server_and_ip(PYHID_CONFIG["board"], config_file_path="config/net_config.json")


@server.route(API_ENDPOINTS["type"], POST)
def type_into_device(request: Request) -> JSONResponse:
    """Type into the device via a simple input string. If no layout is specified, en-US is used."""
    return json_resp(
        request,
        type_chars,
        {"required_keys": {"data": str}, "optional_keys": {"layout": str, "wait": (int, float)}}
    )

@server.route(API_ENDPOINTS["type_keycodes"], POST)
def type_into_device(request: Request) -> JSONResponse:
    """
    Types into the connected device via keycodes, maximum of six pressed at one time.
    Layout is NOT required when interacting directly with keycodes.

    A list of lists can be provided if you wish to enter a sequence of key combinations/keycodes.
    Single key combo:
        {"data": ["CONTROL", "SHIFT", "ESCAPE"]}
    Multiple key combos:
        {"data": [["SHIFT", "KEYPAD_SEVEN"], ["CONTROL", "SHIFT", "ESCAPE"]]}
    Mixture of key combos and single key codes:
        {"data": ["F5", ["SHIFT", "KEYPAD_SEVEN"], ["CONTROL", "SHIFT", "ESCAPE"]]}
    Single key codes in flat list:
        {"data": ["KEYPAD_SEVEN", "C", "ESCAPE"], "separate": True}
    """
    return json_resp(
        request,
        type_keycodes,
        {"required_keys": {"data": list}, "optional_keys": {"wait": (int, float), "separate": bool}}
    )

server.serve_forever(listening_ip)
