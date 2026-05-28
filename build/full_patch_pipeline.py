import sys, io, struct, json, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SECTOR = 2048
os.makedirs("build/packdata_resources", exist_ok=True)

# STEP 1: Font atlas
print("=== STEP 1: Font Atlas ===")
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
print(f"  Font atlas -> {fname} ({len(new_raw)} bytes)")

# STEP 2: Encode + inject translations
print("\n=== STEP 2: Inject Translations ===")
encoded = json.load(open("data/encoded_translations.json", encoding="utf-8"))
by_res = {}
for e in encoded:
    r = e.get("resource")
    if r and isinstance(r, int):
        by_res.setdefault(r, {})[e.get("message", 0)] = e["glyphs"]
print(f"  {sum(len(v) for v in by_res.values())} translations for {len(by_res)} resources")

modified = 0
for res_idx, msg_trans in by_res.items():
    raws = glob.glob(f"extracted/packdata_raw/{res_idx:04d}_type*.raw")
    if not raws: continue
    raw = bytearray(open(raws[0], "rb").read())
    rfn = os.path.basename(raws[0])
    
    # Find stream start
    ss = None
    for i in range(16, min(len(raw)-1, 4000), 2):
        if struct.unpack_from(">H", raw, i)[0] in (0xFFFF, 0xFFFE):
            ss = i; break
    if ss is None: continue
    
    # Parse messages
    msgs = []
    ms = ss; i = ss
    while i < len(raw)-1:
        w = struct.unpack_from(">H", raw, i)[0]
        if w == 0xFFFF:
            msgs.append((ms, i)); ms = i+2
        elif w == 0 and all(raw[j]==0 for j in range(i, min(i+8, len(raw)))):
            msgs.append((ms, i)); break
        i += 2
    
    # Rebuild stream
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
    sub = raw[:16]
    new_sub = struct.pack("<IIII",
        struct.unpack_from("<I", sub, 0)[0], len(payload),
        struct.unpack_from("<I", sub, 8)[0], struct.unpack_from("<I", sub, 12)[0])
    nr = new_sub + payload
    sc = (len(nr)+SECTOR-1)//SECTOR
    nr += b"\x00"*(sc*SECTOR-len(nr))
    open(f"build/packdata_resources/{rfn}", "wb").write(nr)
    modified += 1

print(f"  Modified {modified} resources")

# STEP 3: Rebuild PACKDATA.DIG
print("\n=== STEP 3: Rebuild PACKDATA.DIG ===")
manifest = json.load(open("extracted/packdata_resources/manifest.json", encoding="utf-8"))
with open("extracted/PACKDATA.DIG", "rb") as f:
    otoc = [struct.unpack("<III", f.read(12)) for _ in range(2883)]
    f.seek(0); hdr = f.read(125*SECTOR)

with open("build/PACKDATA.DIG", "wb") as out:
    out.write(hdr)
    cs = 125; ntoc = []
    for entry in manifest:
        idx = entry["index"]
        if entry.get("skipped"):
            ntoc.append(otoc[idx]); continue
        tc = entry["type_code"]
        fn = f"{idx:04d}_type{tc:02d}.raw"
        mp = f"build/packdata_resources/{fn}"
        rp = f"extracted/packdata_raw/{fn}"
        if os.path.exists(mp): d = open(mp,"rb").read()
        elif os.path.exists(rp): d = open(rp,"rb").read()
        else:
            cc = glob.glob(f"extracted/packdata_raw/{idx:04d}_type*.raw")
            d = open(cc[0],"rb").read() if cc else b"\x00"*SECTOR
        sc = (len(d)+SECTOR-1)//SECTOR
        if len(d) < sc*SECTOR: d += b"\x00"*(sc*SECTOR-len(d))
        out.seek(cs*SECTOR); out.write(d)
        ntoc.append((cs, sc, tc)); cs += sc
    out.seek(0)
    for so,sc,tc in ntoc: out.write(struct.pack("<III",so,sc,tc))
    out.seek(0,2); fs = out.tell()

os2 = os.path.getsize("extracted/PACKDATA.DIG")
print(f"  Size: {fs:,} (orig: {os2:,}, diff: {fs-os2:+,})")
print("\n=== PACKDATA.DIG WITH ENGLISH TEXT READY! ===")
print("Next: inject into ISO and generate xdelta patch")
