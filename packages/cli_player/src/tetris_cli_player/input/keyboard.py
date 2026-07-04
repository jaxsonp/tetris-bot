import os
import sys
from queue import Queue
import threading
import atexit
import time

from .terminal import enable_raw_mode, disable_raw_mode

_daemon: threading.Thread | None = None
_input_queue = Queue()
_stop_event = threading.Event()

def start_keyboard_input_daemon() -> Queue:
    """
    Starts the keyboard input daemon in the background. Returns a queue where
    keypresses will be enqueued concurrently.
    """
    global _daemon, _input_queue
    if _daemon is not None:
        return
    
    _daemon = threading.Thread(target=_keyboard_input_daemon, name="keyboard_input_daemon")
    _daemon.start()
    
    return _input_queue

def stop_keyboard_input_daemon():
    if _daemon is None:
        return
    _stop_event.set()



def _keyboard_input_daemon():
    global _input_queue, _stop_event

    atexit.register(disable_raw_mode)

    enable_raw_mode()

    while not _stop_event.is_set():
        if os.name == 'posix':
            import select
            # Wait up to 0.1s for input, then loop to check stop_event
            rlist, _, _ = select.select([sys.stdin], [], [], 0.01)
            if rlist:
                c = sys.stdin.buffer.read(1)
                if c == b'\x1b':
                    # escape sequences
                    seq = sys.stdin.buffer.read(2)
                    if seq == b'[A':
                        _input_queue.put(b"UP")
                    elif seq == b'[B':
                        _input_queue.put(b"DOWN")
                    elif seq == b'[C':
                        _input_queue.put(b"RIGHT")
                    elif seq == b'[D':
                        _input_queue.put(b"LEFT")
                else:
                    # normal characters
                    _input_queue.put(c)
                
                
        elif os.name == 'nt':
            import msvcrt
            if msvcrt.kbhit():
                # getch() returns bytes on Windows, needs decoding
                char = msvcrt.getch()
                _input_queue.put(char)
            else:
                time.sleep(0.01) # Prevent high CPU usage