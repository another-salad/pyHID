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
from adafruit_httpserver.status import BAD_REQUEST_400, INTERNAL_SERVER_ERROR_500
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket  # move to circuit-python-utils?

# USB HID KEYBOARD
import usb_hid
from adafruit_hid.keyboard import Keyboard, Keycode
# Keyboard Layouts
from supported_keyboards import SUPPORTED_KEYBOARDS

# USB HID MOUSE
from adafruit_hid.mouse import Mouse

# circuit-python-utils
from wiznet5keth import NetworkConfig, config_eth
from config_utils import get_config_from_json_file


# config files
ETH_CONFIG = config_eth(NetworkConfig(**get_config_from_json_file("config/net_config.json")))
PYHID_CONFIG = get_config_from_json_file("config/pyhid_config.json")
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


def _type_chars(request, input_data: dict):
    requested_layout = input_data.get("layout", None)
    all_supported_kbds = tuple(SUPPORTED_KEYBOARDS.keys())
    if requested_layout is None:
        Keyboard = SUPPORTED_KEYBOARDS["en-US"]
    elif requested_layout not in all_supported_kbds:
        return JSONResponse(
            request,
            {"error": f"Unsupported keyboard layout: {requested_layout}. Available layouts: {all_supported_kbds}"},
            status=BAD_REQUEST_400
        )
    else:
        Keyboard = SUPPORTED_KEYBOARDS[requested_layout]

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
        return JSONResponse(request, {"error": repr(exc)}, status=BAD_REQUEST_400)


def _press_keys(_keyboard, _keys, wait):
    added_prefix_keys = [getattr(Keycode, _key.upper()) for _key in _keys]
    _keyboard.press(*added_prefix_keys)
    _keyboard.release_all()
    if wait:
        time.sleep(wait)


def _type_keycodes(_, input_data: dict):
    wait = input_data.get("wait", None)
    # Review, might need better error handling for invalid keycodes
    if any(isinstance(x, list) for x in input_data["data"]) or input_data.get("separate", False):
        for keycodes in input_data["data"]:
            _press_keys(kbd, [keycodes] if isinstance(keycodes, str) else keycodes, wait)
    else:
        _press_keys(kbd, input_data["data"], wait)


def _json_resp(request, _callable, validator_kwargs) -> JSONResponse:
    try:
        request_json = request.json()
    except:
        return JSONResponse(request, {"error": "Invalid json data."}, status=BAD_REQUEST_400)
    try:
        bad_input_data = validate_dict(request_json, **validator_kwargs)
        if bad_input_data:
            return JSONResponse(request, {"error": bad_input_data}, status=BAD_REQUEST_400)
        print(request_json)
        res = _callable(request, request_json)
        if isinstance(res, JSONResponse):
            return res
        return JSONResponse(request, {"error": "OK"})
    except Exception as exc:
        return JSONResponse(request, {"error": repr(exc)}, status=INTERNAL_SERVER_ERROR_500)


@server.route(API_ENDPOINTS["type"], POST)
def type_into_device(request: Request) -> JSONResponse:
    """Type into the device"""
    print(request)
    return _json_resp(
        request,
        _type_chars,
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
    return _json_resp(
        request,
        _type_keycodes,
        {"required_keys": {"data": list}, "optional_keys": {"wait": (int, float), "separate": bool}}
    )

server.serve_forever(str(ETH_CONFIG.pretty_ip(ETH_CONFIG.ip_address)))
