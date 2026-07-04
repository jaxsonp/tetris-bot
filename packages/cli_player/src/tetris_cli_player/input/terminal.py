import os
import sys

if os.name == 'posix':
    # posix
    import termios
    import tty

    fd = None
    old_settings = None
        
elif os.name == 'nt':
    # windows
    import ctypes

    handle = None
    old_mode = None

def enable_raw_mode():
    if os.name == 'posix':
        global fd, old_settings

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        tty.setcbreak(fd)
            
    elif os.name == 'nt':
        global handle, old_mode

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-10) # STD_INPUT_HANDLE
        mode = ctypes.c_uint32()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        old_mode = mode.value
        
        # disable ENABLE_LINE_INPUT (0x0002) and ENABLE_ECHO_INPUT (0x0004)
        kernel32.SetConsoleMode(handle, old_mode & ~0x0006)

def disable_raw_mode():
    if os.name == 'posix':
        global fd, old_settings

        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            
    elif os.name == 'nt':
        global handle, old_mode

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-10) # STD_INPUT_HANDLE
        kernel32.SetConsoleMode(handle, old_mode)