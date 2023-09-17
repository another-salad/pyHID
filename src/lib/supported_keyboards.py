"""Contains a dict of supported keyboards and their layouts."""

from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from keyboard_layout_win_uk import KeyboardLayout as KeyboardLayoutUK
from keyboard_layout_win_ca import KeyboardLayout as KeyboardLayoutCA
from keyboard_layout_win_es import KeyboardLayout as KeyboardLayoutES
from keyboard_layout_win_fr import KeyboardLayout as KeyboardLayoutFR
from keyboard_layout_win_de import KeyboardLayout as KeyboardLayoutDE


SUPPORTED_KEYBOARDS = {
    "en-US": KeyboardLayoutUS,
    "en-GB": KeyboardLayoutUK,
    "fr-CA": KeyboardLayoutCA,
    "es-ES": KeyboardLayoutES,
    "de-DE": KeyboardLayoutDE,
    "fr-FR": KeyboardLayoutFR
}
