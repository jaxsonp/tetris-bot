import os
import threading
import enum
from typing import Callable

# from .terminal import enable_raw_mode, disable_raw_mode

if os.name == "posix":
    import evdev
elif os.name == "nt":
    pass
else:
    raise NotImplementedError(f"Unsupported OS: \"{os.name}\"")


_daemon: threading.Thread | None = None


class Key(enum.StrEnum):
    UNKNOWN = enum.auto()
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    SPACE = "space"
    ENTER = "enter"
    L_SHIFT = "lshift"
    R_SHIFT = "rshift"
    L_CTRL = "lctrl"
    ESCAPE = "esc"
    C = "c"
    H = "h"
    Z = "z"
    Q = "q"

def start_keyboard_input_daemon(callback: Callable):
    """
    Starts the keyboard input daemon in the background. Calls the callback with
    like so: `callback(key: keyboard.Key, down: bool)` when a key is pressed or
    released
    """
    global _daemon
    if _daemon is not None:
        return

    if os.name == "posix":
        daemon_func = _posix_keyboard_input_daemon
    elif os.name == "nt":
        daemon_func = _windows_keyboard_input_daemon

    _daemon = threading.Thread(target=daemon_func, args=(callback,), name="keyboard_listener_daemon", daemon=True)
    _daemon.start()


def _posix_keyboard_input_daemon(callback: Callable):

    # find a device that looks like a keyboard
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    keyboard = next((d for d in devices if 'keyboard' in d.name.lower() or 'kbd' in d.name.lower()), None)
    if not keyboard:
        raise RuntimeWarning("No keyboard found in /dev/input/ to read from")

    SCANCODE_TO_KEY: dict[int, Key] = {
        evdev.ecodes.KEY_UP: Key.UP,
        evdev.ecodes.KEY_DOWN: Key.DOWN,
        evdev.ecodes.KEY_RIGHT: Key.RIGHT,
        evdev.ecodes.KEY_LEFT: Key.LEFT,
        evdev.ecodes.KEY_SPACE: Key.SPACE,
        evdev.ecodes.KEY_ENTER: Key.ENTER,
        evdev.ecodes.KEY_LEFTSHIFT: Key.L_SHIFT,
        evdev.ecodes.KEY_RIGHTSHIFT: Key.R_SHIFT,
        evdev.ecodes.KEY_LEFTCTRL: Key.L_CTRL,
        evdev.ecodes.KEY_ESC: Key.ESCAPE,
        evdev.ecodes.KEY_C: Key.C,
        evdev.ecodes.KEY_H: Key.H,
        evdev.ecodes.KEY_Q: Key.Q,
        evdev.ecodes.KEY_Z: Key.Z,
    }
    
    keyboard.grab()
    try:
        for event in keyboard.read_loop():
            if event.type == evdev.ecodes.EV_KEY:
                key_event: evdev.KeyEvent = evdev.categorize(event)
                
                if key_event.keystate == key_event.key_down:
                    callback(SCANCODE_TO_KEY.get(key_event.scancode, Key.UNKNOWN), True)
                elif key_event.keystate == key_event.key_up:
                    callback(SCANCODE_TO_KEY.get(key_event.scancode, Key.UNKNOWN), False)
                # else: # key hold event

    finally:
        keyboard.ungrab()

def _windows_keyboard_input_daemon(callback: Callable):
    # TODO
    raise NotImplementedError()