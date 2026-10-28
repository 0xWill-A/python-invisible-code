import ctypes
import sys
BASE = "\u200b"

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002

payload = "import os; os.system('msg * pretty sure you didnt know about that code')" # DEFAULT PAYLOAD HERE

def encode(text):
    hidden = BASE
    for byte in text.encode("utf-8"):
        if byte < 0x10:
            hidden += chr(0xFE00 + byte)     # U+FE00 -> U+FE0F
        else:
            hidden += chr(0xE0100 + byte - 0x10)  # U+E0100 -> U+E01EF
    return hidden


def _windows_apis():
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
    user32.OpenClipboard.argtypes = [ctypes.c_void_p]
    user32.SetClipboardData.restype = ctypes.c_void_p
    user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
    user32.GetClipboardData.restype = ctypes.c_void_p
    user32.GetClipboardData.argtypes = [ctypes.c_uint]
    return user32, kernel32


def copy_to_clipboard_windows(text):
    user32, kernel32 = _windows_apis()
    data = text.encode("utf-16-le") + b"\x00\x00"
    handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
    if not handle:
        raise OSError("Windows did not give us clipboard memory")
    pointer = kernel32.GlobalLock(handle)
    ctypes.memmove(pointer, data, len(data))
    kernel32.GlobalUnlock(handle)
    if not user32.OpenClipboard(None):
        kernel32.GlobalFree(handle)
        raise OSError("could not open the clipboard (busy with another app?)")
    try:
        user32.EmptyClipboard()
        if not user32.SetClipboardData(CF_UNICODETEXT, handle):
            kernel32.GlobalFree(handle)
            raise OSError("Windows refused the clipboard data")
    finally:
        user32.CloseClipboard()


def read_clipboard_windows():
    user32, kernel32 = _windows_apis()

    if not user32.OpenClipboard(None):
        raise OSError("could not open the clipboard (busy with another app?)")
    try:
        handle = user32.GetClipboardData(CF_UNICODETEXT)
        if not handle:
            return ""
        pointer = kernel32.GlobalLock(handle)
        text = ctypes.wstring_at(pointer)
        kernel32.GlobalUnlock(handle)
        return text
    finally:
        user32.CloseClipboard()


def main():
    global payload
    if len(sys.argv) > 1:
        payload = " ".join(sys.argv[1:])
    elif payload == "":
        payload = 'print("Hello from the invisible side!")'

    hidden = encode(payload)

    try:
        copy_to_clipboard_windows(hidden)
        back = read_clipboard_windows()
        if back.strip() == hidden:
            print("Copied to the clipboard and verified it:")
            print(" ", len(hidden), "invisible characters survived intact.")
        else:
            print("WARNING: the clipboard did NOT keep the characters!, try to copy it from payload_hidden.txt instead")
    except OSError as error:
        print("Clipboard problem:", error)
        print("try to copy it from payload_hidden.txt instead")

    with open("payload_hidden.txt", "w", encoding="utf-8") as f:
        f.write(hidden)
main()