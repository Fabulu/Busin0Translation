import zipfile, os, struct, sys

OUTDIR = r"C:\Programmieren\wizardrytranslation\runs\CLAUDE-RUNS\RUN-20260522-1932-initial-recon\subagents\recon44-kanji-ram"
SAVSTATE = r"C:\Programmieren\wizardrytranslation\randomdialogue.p2s"

with zipfile.ZipFile(SAVSTATE, "r") as z:
    z.extract("eeMemory.bin", OUTDIR)

ram_path = os.path.join(OUTDIR, "eeMemory.bin")
ram_size = os.path.getsize(ram_path)
print(f"RAM dump: {ram_size} bytes ({ram_size/1024/1024:.1f} MB)")

with open(ram_path, "rb") as f:
    ram = f.read()

print("\n=== TASK 1a: Search for SJIS hiragana blocks ===")
hits = []
for offset in range(0, len(ram) - 20, 2):
    vals = [struct.unpack_from("<H", ram, offset + i*2)[0] for i in range(10)]
    hira_count = sum(1 for v in vals if 0x82A0 <= v <= 0x82F1)
    if hira_count >= 7:
        hits.append((offset, vals))

print(f"Found {len(hits)} locations with 7+ hiragana codes in 10 consecutive uint16s")
for h in hits[:30]:
    offset, vals = h
    hex_vals = " ".join(f"{v:04X}" for v in vals)
    chars = []
    for v in vals:
        try:
            b = struct.pack(">H", v)
            c = b.decode("shift_jis")
            chars.append(c)
        except:
            chars.append("?")
    print(f"  0x{offset:08X}: {hex_vals}  [{"".join(chars)}]")

