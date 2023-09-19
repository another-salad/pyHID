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

import os

import microcontroller

from adafruit_httpserver import Request, JSONResponse, GET, POST

# Keyboard Layouts
from supported_keyboards import SUPPORTED_KEYBOARDS

# circuit-python-utils
from config_utils import get_config_from_json_file

# usb_hid_helpers
from usb_hid_helpers import type_chars, type_keycodes, json_resp, json_resp_get
# HTTP server
from create_server import get_server_and_ip

from get_boot_kbd import get_boot_enable_path, BOOT_KBD_DIR

# config files
PYHID_CONFIG = get_config_from_json_file("config/pyhid_config.json")
API_ENDPOINTS = PYHID_CONFIG["api_endpoints"]

# Configure server
server, listening_ip = get_server_and_ip(PYHID_CONFIG["board"], config_file_path="config/net_config.json")


def _disable_boot_keyboard():
    """disabled boot keyboard mode, will need a hard reset for this to take effect"""
    boot_enable_path = get_boot_enable_path()
    if boot_enable_path:
        os.rename(boot_enable_path, f"{BOOT_KBD_DIR}/disable")


def _hard_reset():
    """In a very unfriendly way, this resets the device"""
    microcontroller.reset()


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
        {"data": [["SHIFT", "A"], ["CONTROL", "SHIFT", "ESCAPE"]]}
    Mixture of key combos and single key codes:
        {"data": ["F5", ["SHIFT", "T"], ["CONTROL", "SHIFT", "ESCAPE"]]}
    Single key codes in flat list:
        {"data": ["KEYPAD_FIVE", "C", "ESCAPE"], "separate": True}
    """
    return json_resp(
        request,
        type_keycodes,
        {"required_keys": {"data": list}, "optional_keys": {"wait": (int, float), "separate": bool}}
    )


@server.route(API_ENDPOINTS["disable_boot_keyboard"], GET)
def disable_boot_keyboard(request: Request):
    """This will re-enable serial, USB storage and MIDI and prevent the device from running as a boot keyboard"""
    return json_resp_get(request, _disable_boot_keyboard)


@server.route(API_ENDPOINTS["hard_reset"], GET)
def hard_reset(request: Request):
    """Resets the device, very aggressively. I'll wrap this in a try/except, however don't expect this to actually
    respond. Just wait a few seconds and the device should be back up and running."""
    return json_resp_get(request, _hard_reset)


server.serve_forever(listening_ip)
