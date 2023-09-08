"""Returns the boot enable file in ./boot_kbd (if present)"""

import os

BOOT_KBD_DIR = "boot_kbd"

def get_boot_enable_path() -> str:
    """Returns the path to /boot_kbd/enable if present"""
    boot_enable_path = ""
    kbd_boot_fs = os.listdir(BOOT_KBD_DIR)
    for kbd_file in kbd_boot_fs:
        if "enable" in kbd_file.lower():
            # no os.path in Circuit Python
            boot_enable_path = f"{BOOT_KBD_DIR}/{kbd_file}"
            break

    return boot_enable_path