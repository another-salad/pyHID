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

import time

from adafruit_httpserver import Server, Request, JSONResponse, GET, POST
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket  # move to circuit-python-utils?

# USB HID KEYBOARD
import usb_hid
from adafruit_hid.keyboard import Keyboard, Keycode
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
# CUSTOM KEYBOARDS
from keyboard_layout_win_uk import KeyboardLayout as KeyboardLayoutUK
from keyboard_layout_win_ca import KeyboardLayout as KeyboardLayoutCA
from keyboard_layout_win_es import KeyboardLayout as KeyboardLayoutES
from keyboard_layout_win_fr import KeyboardLayout as KeyboardLayoutFR
from keyboard_layout_win_de import KeyboardLayout as KeyboardLayoutDE
# USB HID MOUSE
from adafruit_hid.mouse import Mouse

# circuit-python-utils
from wiznet5keth import NetworkConfig, config_eth
from config_utils import get_config_from_json_file
from wsgi_web_app_helpers import bad_request, internal_server_error


# config files
ETH_CONFIG = config_eth(NetworkConfig(**get_config_from_json_file("config/net_config.json")))
PYHID_CONFIG = config_eth(NetworkConfig(**get_config_from_json_file("config/pyhid_config.json")))
API_ENDPOINTS = PYHID_CONFIG["api_endpoints"]

socket.set_interface(ETH_CONFIG)  # move to circuit-python-utils?
server = Server(socket, "/static", debug=True)  # html files in static?

# Create Keyboard and Mouse objects
kbd = Keyboard(usb_hid.devices)
mouse = Mouse(usb_hid.devices)


def validate_dict(input_data: dict, required_keys: dict, optional_keys: dict = None) -> dict:
    """
    Validates a dictionary against a required_keys dict and optional_keys dict.
    Returns a dict of bad input data, or an empty dict if all is well.
    """
    bad_input_data = {}
    for key, value in required_keys.items():
        if key not in input_data.keys():
            bad_input_data[key] = "Required key not found"
        elif not isinstance(input_data[key], value):
            bad_input_data[key] = f"Key: {key} must be of type: {value}"
    if optional_keys:
        for key, value in optional_keys.items():
            if key in input_data.keys() and not isinstance(input_data[key], value):
                bad_input_data[key] = f"Key: {key} must be of type: {value}"
    return bad_input_data


def _type_chars(input_data: dict):
    supported_keyboards = PYHID_CONFIG["supported_keyboards"]
    bad_input_data = validate_dict(input_data, {"data": str, "layout": str, "wait": (int, float)})
    if bad_input_data:
        return bad_request(bad_input_data)
    requested_layout = input_data.get("layout", None)
    if requested_layout is None:
        Keyboard = supported_keyboards["en-US"]
    elif requested_layout not in supported_keyboards.keys():
        return bad_request(
            f"Unsupported keyboard layout: {requested_layout}. Available layouts: {tuple(supported_keyboards.keys())}"
          )
    else:
        Keyboard = supported_keyboards[requested_layout]

    layout = Keyboard(kbd)
    wait = input_data.get("wait", None)
    try:
      if wait:  # We have specified a wait per key press
          wait = float(wait)
          for chr in input_data["data"]:
              layout.write(chr)
              time.sleep(wait)
      else:
          layout.write(input_data["data"])
    except Exception as exc:
      return bad_request(repr(exc))

    # TODO:
    # - compatible status codes (Adafruit CircuitPython HTTP Server), bad_request will fail.
    # - Handle 200 status return values (good_request?)

@server.route(API_ENDPOINTS["type"], POST)
def type_into_device(request: Request):
    """Type into the device"""
    request_json = request.json()
    if not request_json:
        return bad_request("No json data found in request.")
    _type_chars(request_json)
    return JSONResponse(request, "Hello from the CircuitPython HTTP Server!")

server.serve_forever(str(ETH_CONFIG.pretty_ip(ETH_CONFIG.ip_address)))
