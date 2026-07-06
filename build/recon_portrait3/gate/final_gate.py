import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'C:/programmieren/wizardrytranslation/tools')
from sec1_disasm import walk
HEADER=0x20
def sec1(p):
    d=open(p,'rb').read(); s2=struct.unpack_from('<I',d,0x18)[0]; return d[HEADER:s2]
CUR='C:/programmieren/wizardrytranslation/build/packdata_resources/1196_type02.raw'
s=sec1(CUR); ok,instrs=walk(s)
# 0x2B at 0x79C: 002b 0005 0006 0016 0001 ...  word@6=0x0016 = portrait/char id
# 0x0C at 0x16: 000c 0000 001e  -> param0 idx 0x1E=30
# Show the instruction window from start to first 2B with all opcodes
print("Section-1 prologue opcodes (pc 0x00..0x80):")
for pc in sorted(instrs):
    if pc>0xCC: break
    op=instrs[pc]
    print(f"  pc=0x{pc:04X} op=0x{op:02X} bytes={s[pc:pc+8].hex()}")
# The 0x2B emit ids
print("\n0x2B portrait emits (word@6 = char/portrait slot id):")
seen=set()
for pc in sorted(instrs):
    if instrs[pc]==0x2B:
        w=struct.unpack_from('>5H',s,pc)
        if w[3] not in seen:
            seen.add(w[3])
            print(f"  pc=0x{pc:04X} ids: w1={w[1]} w2={w[2]} portraitId=0x{w[3]:04X}({w[3]}) w4={w[4]}")
