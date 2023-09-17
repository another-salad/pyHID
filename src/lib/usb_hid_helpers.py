"""Helper functions that allow user input to be pumped through the pyHID device."""

import time

# USB HID KEYBOARD
import usb_hid

from adafruit_hid.keyboard import Keyboard, Keycode
from adafruit_hid.mouse import Mouse

from adafruit_httpserver import JSONResponse
from adafruit_httpserver.status import BAD_REQUEST_400, INTERNAL_SERVER_ERROR_500

# Keyboard Layouts
from supported_keyboards import SUPPORTED_KEYBOARDS


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


def _press_keys(_keyboard, _keys, wait):
    """Calls the USB HID keyboard press method to input a list of keycodes."""
    added_prefix_keys = [getattr(Keycode, _key.upper()) for _key in _keys]
    try:
        _keyboard.press(*added_prefix_keys)
    finally:
        _keyboard.release_all()
    if wait:
        time.sleep(wait)


def type_chars(request, input_data: dict):
    """Type into the device via a simple input string. If no layout is specified, en-US is used."""
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
        try:
            # Try to release all keys, just in case. Little hideous, but safety first.
            layout.release_all()
        except:
            pass
        return JSONResponse(request, {"error": repr(exc)}, status=BAD_REQUEST_400)


def type_keycodes(_, input_data: dict):
    """
    Types into the connected device via keycodes, maximum of six pressed at one time.
    """
    wait = input_data.get("wait", None)
    # Review, might need better error handling for invalid keycodes
    if any(isinstance(x, list) for x in input_data["data"]) or input_data.get("separate", False):
        for keycodes in input_data["data"]:
            _press_keys(kbd, [keycodes] if isinstance(keycodes, str) else keycodes, wait)
    else:
        _press_keys(kbd, input_data["data"], wait)


def json_resp(request, _callable, validator_kwargs: dict) -> JSONResponse:
    """
    A wrapper that handles json input validation and returns a JSONResponse object.
    """
    try:
        request_json = request.json()
    except:
        return JSONResponse(request, {"error": "Invalid json data."}, status=BAD_REQUEST_400)
    try:
        bad_input_data = validate_dict(request_json, **validator_kwargs)
        if bad_input_data:
            return JSONResponse(request, {"error": bad_input_data}, status=BAD_REQUEST_400)
        res = _callable(request, request_json)
        if isinstance(res, JSONResponse):
            return res
        return JSONResponse(request, {"error": "OK"})
    except Exception as exc:
        return JSONResponse(request, {"error": repr(exc)}, status=INTERNAL_SERVER_ERROR_500)


def json_resp_get(request, _callable) -> JSONResponse:
    """A wrapper that will always a return a JSONResponse object, but handles no input data."""
    try:
        # a little copy/pasta here. NOTE: can we do less bad?
        res = _callable()
        if isinstance(res, JSONResponse):
            return res
        return JSONResponse(request, {"error": "OK"})
    except Exception as exc:
        return JSONResponse(request, {"error": repr(exc)}, status=INTERNAL_SERVER_ERROR_500)
