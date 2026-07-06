import sys, struct, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools')
from sec1_disasm import walk
opt=json.load(open('build/recon_v85/exe-interpreter/opcode_table_v85.json'))['opcodes']
def oplen(op): return opt.get('0x%02X'%op,{}).get('bytes',2)
def sec1(path):
    d=open(path,'rb').read(); s2=struct.unpack_from('<I',d,0x18)[0]; return d[0x20:s2]
for tag,p in (('CUR','build/packdata_resources/1197_type02.raw'),('JP','extracted/packdata_raw/1197_type02.raw')):
    s=sec1(p); ok,ins=walk(s)
    print(f"=== {tag} GOSUB target 0x10B4 ===")
    for pc in sorted(ins):
        if 0x10B4<=pc<0x1120:
            op=ins[pc]; n=oplen(op); print(f"  0x{pc:04X} op=0x{op:02X} {s[pc:pc+n].hex()}")
    print()
