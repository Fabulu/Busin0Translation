import sys, io, struct, json, glob, os, shutil
import locale; pass
sys.path.insert(0, "tools")
from encode_english_text import encode_text, table

SECTOR = 2048
print("=== BUILDING FULL ENGLISH PATCH ===\n")

# STEP 1: Merge all translation chunks
print("Step 1: Merging translations...")
all_trans = []
for i in range(10):
    f = f"data/translate_chunks/chunk_{i:02d}_translated.json"
    chunk = json.load(open(f, encoding="utf-8"))
    all_trans.extend(chunk)
print(f"  {len(all_trans)} total translations")

# STEP 2: Encode all English text to glyph streams
print("Step 2: Encoding English text...")
encoded_by_res = {}
errors = 0
for entry in all_trans:
    english = entry.get("english", "")
    if not english:
        continue
    try:
        glyphs = encode_text(english, max_chars_per_line=18, max_lines_per_page=3)
        res = entry.get("resource")
        msg = entry.get("message")
        if res is not None and msg is not None:
            encoded_by_res.setdefault(int(res), {})[int(msg)] = glyphs
    except Exception as e:
        errors += 1

total_encoded = sum(len(v) for v in encoded_by_res.values())
print(f"  Encoded {total_encoded} messages for {len(encoded_by_res)} resources ({errors} errors)")

# STEP 3: Inject font atlas
print("Step 3: Injecting font atlas...")
os.makedirs("build/packdata_resources", exist_ok=True)
font_data = open("build/english_font_atlas.bin", "rb").read()
raw_1272 = glob.glob("extracted/packdata_raw/1272_type*.raw")[0]
orig_raw = open(raw_1272, "rb").read()
sub = orig_raw[:16]
new_sub = struct.pack("<IIII",
    struct.unpack_from("<I", sub, 0)[0], len(font_data),
    struct.unpack_from("<I", sub, 8)[0], struct.unpack_from("<I", sub, 12)[0])
new_raw = new_sub + font_data
sc = (len(new_raw) + SECTOR-1) // SECTOR
new_raw += b"\x00" * (sc*SECTOR - len(new_raw))
fname = os.path.basename(raw_1272)
open(f"build/packdata_resources/{fname}", "wb").write(new_raw)
print(f"  Font atlas injected")

# STEP 4: Inject translations into MSG resources
print("Step 4: Injecting translations...")
modified = 0
for res_idx, msg_trans in encoded_by_res.items():
    raws = glob.glob(f"extracted/packdata_raw/{res_idx:04d}_type*.raw")
    if not raws:
        continue
    raw = bytearray(open(raws[0], "rb").read())
    rfn = os.path.basename(raws[0])
    sub_header = raw[:16]

    ss = None
    for i in range(16, min(len(raw)-1, 4000), 2):
        if struct.unpack_from(">H", raw, i)[0] in (0xFFFF, 0xFFFE):
            ss = i
            break
    if ss is None:
        continue

    msgs = []
    ms = ss
    i = ss
    while i < len(raw)-1:
        w = struct.unpack_from(">H", raw, i)[0]
        if w == 0xFFFF:
            msgs.append((ms, i))
            ms = i+2
        elif w == 0 and all(raw[j]==0 for j in range(i, min(i+8, len(raw)))):
            msgs.append((ms, i))
            break
        i += 2

    ns = bytearray()
    for mi, (s, e) in enumerate(msgs):
        if mi in msg_trans:
            for g in msg_trans[mi]:
                ns += struct.pack(">H", g)
        else:
            ns += raw[s:e]
        ns += struct.pack(">H", 0xFFFF)

    pre = raw[16:ss]
    payload = pre + ns
    new_sub = struct.pack("<IIII",
        struct.unpack_from("<I", sub_header, 0)[0], len(payload),
        struct.unpack_from("<I", sub_header, 8)[0], struct.unpack_from("<I", sub_header, 12)[0])
    nr = new_sub + payload
    sc = (len(nr)+SECTOR-1)//SECTOR
    nr += b"\x00"*(sc*SECTOR-len(nr))
    open(f"build/packdata_resources/{rfn}", "wb").write(nr)
    modified += 1

print(f"  Modified {modified} resources")

# STEP 5: Rebuild PACKDATA.DIG
print("Step 5: Rebuilding PACKDATA.DIG...")
manifest = json.load(open("extracted/packdata_resources/manifest.json", encoding="utf-8"))
with open("extracted/PACKDATA.DIG", "rb") as f:
    otoc = [struct.unpack("<III", f.read(12)) for _ in range(2883)]
    f.seek(0)
    hdr = f.read(125*SECTOR)

with open("build/PACKDATA.DIG", "wb") as out:
    out.write(hdr)
    cs = 125
    ntoc = []
    for entry in manifest:
        idx = entry["index"]
        if entry.get("skipped"):
            ntoc.append(otoc[idx])
            continue
        tc = entry["type_code"]
        fn = f"{idx:04d}_type{tc:02d}.raw"
        mp = f"build/packdata_resources/{fn}"
        rp = f"extracted/packdata_raw/{fn}"
        if os.path.exists(mp):
            d = open(mp, "rb").read()
        elif os.path.exists(rp):
            d = open(rp, "rb").read()
        else:
            cc = glob.glob(f"extracted/packdata_raw/{idx:04d}_type*.raw")
            d = open(cc[0], "rb").read() if cc else b"\x00"*SECTOR
        sc = (len(d)+SECTOR-1)//SECTOR
        if len(d) < sc*SECTOR:
            d += b"\x00"*(sc*SECTOR-len(d))
        out.seek(cs*SECTOR)
        out.write(d)
        ntoc.append((cs, sc, tc))
        cs += sc
    out.seek(0)
    for so,sc,tc in ntoc:
        out.write(struct.pack("<III",so,sc,tc))
    out.seek(0,2)
    fs = out.tell()

orig_size = os.path.getsize("extracted/PACKDATA.DIG")
print(f"  Size: {fs:,} (orig: {orig_size:,}, diff: {fs-orig_size:+,})")

# Pad to original size for ISO replacement
if fs < orig_size:
    with open("build/PACKDATA.DIG", "ab") as f:
        f.write(b"\x00" * (orig_size - fs))
    print(f"  Padded to {orig_size:,}")

# STEP 6: Build ISO
print("Step 6: Building ISO...")
ISO_PATH = "Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso"
OUTPUT_ISO = "build/BUSIN0_EN.iso"

shutil.copy2(ISO_PATH, OUTPUT_ISO)

import pycdlib
iso = pycdlib.PyCdlib()
iso.open(ISO_PATH)
extent = None
for child in iso.list_children(iso_path="/"):
    if child.is_dot() or child.is_dotdot():
        continue
    if b"PACKDATA" in child.file_identifier():
        extent = child.extent_location()
        break
iso.close()

print(f"  PACKDATA.DIG at ISO extent {extent}")
with open(OUTPUT_ISO, "r+b") as iso_file:
    iso_file.seek(extent * 2048)
    with open("build/PACKDATA.DIG", "rb") as pd:
        while True:
            chunk = pd.read(4 * 1024 * 1024)
            if not chunk:
                break
            iso_file.write(chunk)

print(f"  ISO written: {OUTPUT_ISO}")
print(f"  Size: {os.path.getsize(OUTPUT_ISO):,} bytes")
print(f"\n{'='*50}")
print(f"=== FULL ENGLISH ISO READY! ===")
print(f"=== {total_encoded} messages translated ===")
print(f"=== Try: build/BUSIN0_EN.iso ===")
print(f"{'='*50}")
