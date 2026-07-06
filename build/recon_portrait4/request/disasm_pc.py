import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools')
from sec1_disasm import walk
import json
def sec1(path):
    d=open(path,'rb').read(); s2=struct.unpack_from('<I',d,0x18)[0]; return d[0x20:s2]
js=sec1('extracted/packdata_raw/1197_type02.raw')
cs=sec1('build/packdata_resources/1197_type02.raw')
# load opcode length table
opt=json.load(open('build/recon_v85/exe-interpreter/opcode_table_v85.json'))
# opt maps opcode->length? inspect
print("opt sample:", list(opt.items())[:5] if isinstance(opt,dict) else opt[:5])
jok,ji=walk(js); cok,ci=walk(cs)
PC=0x5320
# print instructions in window around PC for CUR
def dump(s,instrs,tag,center,rad=0x60):
    print(f"--- {tag} around 0x{center:X} ---")
    pcs=[pc for pc in sorted(instrs) if center-rad<=pc<=center+rad]
    for pc in pcs:
        op=instrs[pc]
        raw=s[pc:pc+16]
        mark=' <== PC' if pc==center else ''
        print(f"  0x{pc:04X} op=0x{op:02X} {raw.hex()}{mark}")
dump(cs,ci,'CUR',PC)
print()
dump(js,ji,'JP',PC)
