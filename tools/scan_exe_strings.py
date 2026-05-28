import sys, io, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

data = open("extracted/SLPM_653.78", "rb").read()

def scan_ascii(data, min_len=4):
    hits = []
    i = 0
    while i < len(data):
        if 0x20 <= data[i] <= 0x7E:
            start = i
            while i < len(data) and 0x20 <= data[i] <= 0x7E:
                i += 1
            s = data[start:i].decode("ascii")
            if len(s) >= min_len:
                hits.append((start, "ASCII", s))
        else:
            i += 1
    return hits

def scan_sjis(data, min_chars=3):
    hits = []
    i = 0
    while i < len(data):
        b = data[i]
        if (0x81 <= b <= 0x9F) or (0xE0 <= b <= 0xEF):
            if i + 1 < len(data):
                b2 = data[i+1]
                if (0x40 <= b2 <= 0x7E) or (0x80 <= b2 <= 0xFC):
                    start = i
                    buf = bytearray()
                    while i < len(data):
                        b = data[i]
                        if 0x20 <= b <= 0x7E:
                            buf.append(b); i += 1
                        elif i+1 < len(data) and ((0x81 <= b <= 0x9F) or (0xE0 <= b <= 0xEF)):
                            b2 = data[i+1]
                            if (0x40 <= b2 <= 0x7E) or (0x80 <= b2 <= 0xFC):
                                buf.extend([b, b2]); i += 2
                            else: break
                        elif b in (0x0A, 0x0D): buf.append(b); i += 1
                        else: break
                    if len(buf) >= min_chars * 2:
                        try:
                            text = buf.decode("shift_jis")
                            if any("\u3040" <= c <= "\u30ff" or "\u4e00" <= c <= "\u9fff" or "\uff01" <= c <= "\uff5e" for c in text):
                                hits.append((start, "SJIS", text))
                        except: pass
                    continue
        i += 1
    return hits

def categorize(offset, enc, text):
    cats = []
    tl = text.lower()
    if any(ext in tl for ext in [".dig", ".dsi", ".lzh", ".irx", ".img", ".tim", ".bin", ".dat"]): cats.append("FILE_PATH")
    if "%" in text and any(c in text for c in "dsfxXulp"): cats.append("FORMAT_STR")
    if any(w in tl for w in ["error", "warning", "assert", "fail", "debug"]): cats.append("DEBUG")
    if any(w in tl for w in ["pack", "data", "load", "read", "open", "file", "seek"]): cats.append("FILE_IO")
    if any(w in tl for w in ["font", "char", "glyph", "text", "msg", "str"]): cats.append("TEXT_SYSTEM")
    if any(w in tl for w in ["menu", "item", "spell", "magic", "equip", "weapon"]): cats.append("GAME_DATA")
    if enc == "SJIS" and len(text) > 10: cats.append("GAME_TEXT")
    if not cats: cats.append("OTHER")
    return ",".join(cats)

ascii_hits = scan_ascii(data)
sjis_hits = scan_sjis(data)
all_hits = sorted(ascii_hits + sjis_hits, key=lambda x: x[0])

print(f"Total: {len(ascii_hits)} ASCII + {len(sjis_hits)} SJIS = {len(all_hits)} strings")
print("="*80)

for off, enc, text in all_hits:
    cat = categorize(off, enc, text)
    clean = text.replace("\n", "\n").replace("\r", "\r")
    print(f"0x{off:08X} [{enc:5s}] [{cat}] {clean}")
