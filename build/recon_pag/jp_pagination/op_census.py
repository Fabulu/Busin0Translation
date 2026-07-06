import sys, os, struct, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('tools'))
from sec1_disasm import walk
HEADER_SIZE=0x20
def load_sec(d):
    s=struct.unpack_from('<I',d,0x14)[0]; o=struct.unpack_from('<I',d,0x18)[0]
    return bytes(d[HEADER_SIZE:o]), bytes(d[o:o+s])
for rid in [1196,1197,1205,1211]:
    f=f'extracted/packdata_raw/{rid:04d}_type02.raw'
    d=open(f,'rb').read(); sec1,sec2=load_sec(d)
    ok,instrs=walk(sec1)
    from collections import Counter
    c=Counter(instrs.values())
    print(f"R{rid}: op21={c.get(0x21,0)} op22={c.get(0x22,0)} op04={c.get(0x04,0)} op14={c.get(0x14,0)} op0C={c.get(0x0C,0)} op0D={c.get(0x0D,0)}")
