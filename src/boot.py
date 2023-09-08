import os
import usb_hid
import storage
import usb_cdc
import usb_midi

if "enable" in [x.lower() for x in os.listdir("boot_kbd")]:
    storage.disable_usb_drive()  # disable CIRCUITPY USB storage
    storage.remount("/", False)  # enable Pico's file system to be writable by circuit python
    usb_cdc.disable()            # disable REPL
    usb_midi.disable()           # disable MIDI
    usb_hid.enable((usb_hid.Device.KEYBOARD, usb_hid.Device.MOUSE), boot_device=1)
