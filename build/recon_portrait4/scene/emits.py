import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'C:/programmieren/wizardrytranslation/tools')
from sec1_disasm import walk
HEADER=0x20
def sec1(p):
    d=open(p,'rb').read(); s2=struct.unpack_from('<I',d,0x18)[0]; return d[HEADER:s2]
for tag,p in (('R1196','C:/programmieren/wizardrytranslation/build/packdata_resources/1196_type02.raw'),
              ('R1197','C:/programmieren/wizardrytranslation/build/packdata_resources/1197_type02.raw')):
    s=sec1(p); ok,instrs=walk(s)
    print(f"==== {tag} sec1 len={len(s)} walk_ok={ok} ninstr={len(instrs)} ====")
    # 0x2B portrait emits
    print("  0x2B emits (w1,w2,portraitId,w4):")
    for pc in sorted(instrs):
        if instrs[pc]==0x2B:
            w=struct.unpack_from('>5H',s,pc)
            print(f"    pc=0x{pc:04X} w1={w[1]} w2={w[2]} portraitId=0x{w[3]:04X}({w[3]}) w4={w[4]} bytes={s[pc:pc+12].hex()}")
    # 0x0C sets
    print("  0x0C SET_NAME_REF (param->idx):")
    cset={}
    for pc in sorted(instrs):
        if instrs[pc]==0x0C:
            o,param,idx=struct.unpack_from('>HHH',s,pc); cset.setdefault(param,[]).append(idx)
    for param in sorted(cset): print(f"    param={param}: idx {sorted(cset[param])}")
    # 0x17/0x18 tests
    print("  0x17/0x18 TEST:")
    for pc in sorted(instrs):
        if instrs[pc] in (0x17,0x18):
            w=struct.unpack_from('>6H',s,pc)
            print(f"    pc=0x{pc:04X} op=0x{instrs[pc]:02X} words={[hex(x) for x in w]}")
