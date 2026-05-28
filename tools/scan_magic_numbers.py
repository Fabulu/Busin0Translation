import sys, io, struct, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

FILEPATH = "extracted/PACKDATA.DIG"
FILESIZE = os.path.getsize(FILEPATH)
CHUNK = 16 * 1024 * 1024  # 16MB

SIGNATURES = {
    b"TIM2": "TIM2_TEXTURE",
    b"\x00TIM": "TIM_TEXTURE",
    b"RIFF": "RIFF_AUDIO",
    b"VAGp": "VAG_AUDIO",
    b"\x89PNG": "PNG_IMAGE",
    b"-lh": "LZH_ARCHIVE",
    b"PK\x03\x04": "ZIP_ARCHIVE",
    b"\x00\x00\x01\xba": "MPEG_PS",
    b"\x00\x00\x01\xb3": "MPEG_SEQ",
}

ZLIB_HEADS = [b"\x78\x9c", b"\x78\xda", b"\x78\x01", b"\x78\x5e"]

results = {}
zlib_count = 0

with open(FILEPATH, "rb") as f:
    offset = 0
    prev_tail = b""
    while offset < FILESIZE:
        chunk = f.read(CHUNK)
        if not chunk: break
        data = prev_tail + chunk
        search_start = len(prev_tail)

        for sig, name in SIGNATURES.items():
            pos = 0
            while True:
                pos = data.find(sig, pos)
                if pos == -1: break
                abs_off = offset - len(prev_tail) + pos
                if name not in results: results[name] = []
                results[name].append(abs_off)
                pos += 1

        for zh in ZLIB_HEADS:
            pos = search_start
            while True:
                pos = data.find(zh, pos)
                if pos == -1: break
                abs_off = offset - len(prev_tail) + pos
                zlib_count += 1
                if "ZLIB" not in results: results["ZLIB"] = []
                if len(results["ZLIB"]) < 200:
                    results["ZLIB"].append(abs_off)
                pos += 1

        prev_tail = chunk[-8:] if len(chunk) >= 8 else chunk
        offset += len(chunk)
        mb = offset // (1024*1024)
        if mb % 50 == 0:
            print(f"Scanned {mb}MB / {FILESIZE//(1024*1024)}MB...", file=sys.stderr)

print(f"File: {FILEPATH} ({FILESIZE:,} bytes)")
print("="*80)
for name in sorted(results.keys()):
    offsets = results[name]
    print(f"\n{name}: {len(offsets)} occurrences")
    for o in offsets[:30]:
        print(f"  0x{o:08X} ({o:,})")
    if len(offsets) > 30:
        print(f"  ... and {len(offsets)-30} more")

if zlib_count > 200:
    print(f"\nZLIB total: {zlib_count} (showing first 200)")
