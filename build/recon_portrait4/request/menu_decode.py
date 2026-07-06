import sys, struct, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools')
from sec1_disasm import walk
opt=json.load(open('build/recon_v85/exe-interpreter/opcode_table_v85.json'))['opcodes']
def oplen(op): return opt.get('0x%02X'%op,{}).get('bytes',2)
def sec1(path):
    d=open(path,'rb').read(); s2=struct.unpack_from('<I',d,0x18)[0]; return d[0x20:s2]
cs=sec1('build/packdata_resources/1197_type02.raw')
js=sec1('extracted/packdata_raw/1197_type02.raw')
def show(s,tag,lo,hi):
    print(f"=== {tag} 0x{lo:X}..0x{hi:X} ===")
    ok,ins=walk(s)
    for pc in sorted(ins):
        if not(lo<=pc<hi): continue
        op=ins[pc]; n=oplen(op); raw=s[pc:pc+n]
        # decode operands generically
        print(f"  0x{pc:04X} op=0x{op:02X} ({n}b) {raw.hex()}")
# The menu block is 0x534E..0x5390 (the 0x43/0x45/0x46/0x14 cluster)
show(cs,'CUR',0x534E,0x53A0)
print()
show(js,'JP',0x534E,0x53A0)
