import sys, struct, importlib.util
sys.stdout.reconfigure(encoding='utf-8')

# import dec() from the canonical decoder
spec = importlib.util.spec_from_file_location("dec_mod", r"C:\programmieren\wizardrytranslation\build\_recon_2f2490\dec.py")
# dec.py runs its own loop on import; suppress by reading source & exec only the function part
src = open(r"C:\programmieren\wizardrytranslation\build\_recon_2f2490\dec.py").read()
src = src.split("start=0x2F2490")[0]  # drop the trailing driver loop
ns = {}
exec(src, ns)
dec = ns["dec"]
VA_BASE = 0xFFF80

PATCHED = r"C:\programmieren\wizardrytranslation\build\SLPM_653.78_patched"
PRISTINE = r"C:\programmieren\wizardrytranslation\extracted\SLPM_653.78"

def dump(path, start, end, tag):
    exe = open(path, 'rb').read()
    print(f"\n===== {tag}  [{path.split(chr(92))[-1]}]  VA {start:#X}..{end:#X} =====")
    va = start
    while va < end:
        w = struct.unpack('<I', exe[va - VA_BASE:va - VA_BASE + 4])[0]
        print(f"{va:08X}  {w:08X}  {dec(w, va)}")
        va += 4

which = sys.argv[1] if len(sys.argv) > 1 else "all"
if which in ("hooks", "all"):
    dump(PATCHED, 0x305980, 0x3059B0, "PATCHED HOOK NS_A region (0x305988)")
    dump(PATCHED, 0x3059F0, 0x305A20, "PATCHED HOOK NS_B region (0x3059F8)")
if which in ("caveA", "all"):
    dump(PATCHED, 0x4C7860, 0x4C78A4, "PATCHED CAVE NS_A (0x4C7860)")
if which in ("caveB", "all"):
    dump(PATCHED, 0x4CAA30, 0x4CAA74, "PATCHED CAVE NS_B (0x4CAA30)")
if which in ("tbl", "all"):
    exe = open(PATCHED, 'rb').read()
    base = 0x4C7564 - VA_BASE
    print("\n===== Patch-14 ADV table @0x4C7564 (gid 0..95) =====")
    vals = list(exe[base:base + 96])
    print("space(0):", vals[0], " A(33):", vals[33], " m(77):", vals[77], " z(90):", vals[90])
if which in ("reach", "all"):
    # scan a wide region for any branch/jump whose target lands inside displaced ranges
    exe = open(PATCHED, 'rb').read()
    ranges = [(0x305988, 0x30599C, "NS_A displaced"), (0x3059F8, 0x305A0C, "NS_B displaced")]
    print("\n===== REACHABILITY scan 0x305000..0x306200 =====")
    hits = 0
    va = 0x305000
    while va < 0x306200:
        w = struct.unpack('<I', exe[va - VA_BASE:va - VA_BASE + 4])[0]
        op = (w >> 26) & 0x3F
        tgt = None
        if op in (0x04, 0x05, 0x06, 0x07, 0x01):  # branches
            imm = w & 0xFFFF
            s = imm - 0x10000 if imm & 0x8000 else imm
            tgt = va + 4 + s * 4
        elif op in (0x02, 0x03):  # j / jal
            tgt = ((w & 0x03FFFFFF) << 2) | (va & 0xF0000000)
        if tgt is not None:
            for lo, hi, name in ranges:
                if lo < tgt < hi:  # strictly inside (lo itself is the legit hook entry)
                    print(f"  HIT {va:08X} {dec(w,va)} -> {tgt:08X} inside {name}")
                    hits += 1
                # also flag landing exactly at hi (return point) for info
        va += 4
    print(f"  inbound branches strictly inside displaced ranges: {hits}")
