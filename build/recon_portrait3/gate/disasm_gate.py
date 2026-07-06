import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'C:/programmieren/wizardrytranslation/tools')
from sec1_disasm import walk

JP   = 'C:/programmieren/wizardrytranslation/extracted/packdata_raw/1196_type02.raw'
CUR  = 'C:/programmieren/wizardrytranslation/build/packdata_resources/1196_type02.raw'

HEADER=0x20
def sec1_of(data):
    sec2_off=struct.unpack_from('<I',data,0x18)[0]
    return data[HEADER:sec2_off], sec2_off

def show(path,tag):
    data=open(path,'rb').read()
    sec1,sec2off=sec1_of(data)
    ok,instrs=walk(sec1)
    print(f"\n===== {tag} ({path.split('/')[-1]}) sec1 len={len(sec1)} sec2_off=0x{sec2off:X} walk_ok={ok} ninstr={len(instrs)} =====")
    rows=[]
    for pc,opc in sorted(instrs.items()):
        if opc in (0x0C,0x0D,0x17,0x18):
            raw=bytes(sec1[pc:pc+12])
            rows.append((pc,opc,raw))
    for pc,opc,raw in rows:
        be=lambda o: struct.unpack_from('>H',raw,o)[0] if o+2<=len(raw) else 0
        print(f"  pc=0x{pc:04X} op=0x{opc:02X} bytes={raw.hex()}  w@0={be(0):#06x} w@2={be(2):#06x} w@4={be(4):#06x} w@6={be(6):#06x}")
    return instrs, sec1

ji,js = show(JP,'JP-original')
ci,cs = show(CUR,'CURRENT-build')

print("\n===== SEC1 byte diff JP vs CUR =====")
if js==cs:
    print("  IDENTICAL")
else:
    print(f"  lengths JP={len(js)} CUR={len(cs)}")
    n=min(len(js),len(cs))
    diffs=[i for i in range(n) if js[i]!=cs[i]]
    print(f"  {len(diffs)} differing bytes in common region; first 30: {diffs[:30]}")
    for i in diffs[:30]:
        print(f"    off 0x{i:04X}: JP={js[i]:02x} CUR={cs[i]:02x}")
