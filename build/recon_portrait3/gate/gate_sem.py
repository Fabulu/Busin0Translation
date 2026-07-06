import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'C:/programmieren/wizardrytranslation/tools')
from sec1_disasm import walk
HEADER=0x20
def sec1(p):
    d=open(p,'rb').read(); s2=struct.unpack_from('<I',d,0x18)[0]; return d[HEADER:s2]
CUR='C:/programmieren/wizardrytranslation/build/packdata_resources/1196_type02.raw'
s=sec1(CUR)
ok,instrs=walk(s)

# Decode every 0x0C (SET) and 0x17/0x18 (TEST) with full semantics.
# Per prompt: 0x0C SET_NAME_REF sets channel bit at table[param0]/[param1]/[param2]
#   EXE 0x302020: table[param][idx>>5] |= 1<<(idx&31)
# bytes layout observed: 000c PPPP IIII  -> op=000c, param=PPPP, idx=IIII (BE u16 each), len=6
# 0x17/0x18 layout: 0017 PPPP ???? IIII  -> 6 BE-u16? observed bytes 0017 0000 0001 006b 0000 0001
print("=== 0x0C SET_NAME_REF (param, idx -> sets table[param] bit idx) ===")
cset={}
for pc in sorted(instrs):
    if instrs[pc]==0x0C:
        op,param,idx=struct.unpack_from('>HHH',s,pc)
        cset.setdefault(param,[]).append(idx)
for param in sorted(cset):
    print(f"  table param={param}: sets bits {sorted(cset[param])}")

print("\n=== 0x17 / 0x18 TEST opcodes (full 12 bytes) ===")
for pc in sorted(instrs):
    if instrs[pc] in (0x17,0x18):
        w=struct.unpack_from('>6H',s,pc)
        print(f"  pc=0x{pc:04X} op=0x{instrs[pc]:02X} words={[hex(x) for x in w]}")

# Are there opcode 0x2B (portrait BITBLT emit) in sec1?
print("\n=== 0x2B (portrait emit) occurrences ===")
c2b=[pc for pc in sorted(instrs) if instrs[pc]==0x2B]
print(f"  count={len(c2b)} pcs={[hex(x) for x in c2b[:20]]}")
for pc in c2b[:8]:
    print(f"    pc=0x{pc:04X} bytes={s[pc:pc+16].hex()}")
