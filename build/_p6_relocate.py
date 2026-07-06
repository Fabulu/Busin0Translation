exe = open('extracted/SLPM_653.78','rb').read()
def fo(va): return va - 0x100000 + 0x80
import zipfile
ee = zipfile.ZipFile('ramdumps/unpatchedfight.p2s').read('eeMemory.bin')

# 1) Confirm stock-EXE-FILE zeros vs LIVE-RAM data at 0x4B0DD0 (proves runtime write)
print("=== 0x4B0DD0 region: stock EXE FILE vs LIVE stock RAM ===")
for va in [0x4B0DD0,0x4B0DD8]:
    print(f" VA {hex(va)}: EXEfile={exe[fo(va):fo(va)+4].hex()}  liveRAM={ee[va:va+4].hex()}")

# 2) Patch 27's known-safe relocation target 0x4AB554 — verify it's dead in stock RAM
print("\n=== Candidate safe .text padding (must be ZERO in live stock RAM) ===")
for va in [0x4AB554, 0x4AB560, 0x4AB580, 0x4AB600]:
    fz = all(b==0 for b in exe[fo(va):fo(va)+64])
    rz = all(b==0 for b in ee[va:va+64])
    print(f" VA {hex(va)}: EXEfile_64_zero={fz}  liveRAM_64_zero={rz}")

# 3) Scan .text (0x100000..0x4B0DCF) for a 64-byte all-zero run that is ALSO zero in live RAM
print("\n=== Searching .text for >=64B run zero in BOTH file and live RAM ===")
found=[]
va=0x4A0000
while va < 0x4B0D00 and len(found)<6:
    seg_f = exe[fo(va):fo(va)+64]
    seg_r = ee[va:va+64]
    if all(b==0 for b in seg_f) and all(b==0 for b in seg_r):
        found.append(va)
        va += 64
    else:
        va += 16
for v in found:
    print("  safe-zero run at", hex(v))
