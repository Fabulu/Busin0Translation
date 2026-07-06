import sys, os, struct, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('tools'))
from sec1_disasm import walk, extract_records
HEADER_SIZE=0x20
opt=json.load(open('build/recon_v85/exe-interpreter/opcode_table_v85.json'))['opcodes']
LEN={int(k,16):v['bytes'] for k,v in opt.items()}
def load_sec(d):
    s=struct.unpack_from('<I',d,0x14)[0]; o=struct.unpack_from('<I',d,0x18)[0]
    return bytes(d[HEADER_SIZE:o]), bytes(d[o:o+s])
def parse_groups(sec2):
    n=len(sec2)//2; words=[struct.unpack_from('>H',sec2,i*2)[0] for i in range(n)]
    groups=[];start=0
    for i,w in enumerate(words):
        if w==0xFFFF: groups.append((start,i)); start=i+1
    return groups,words,start
def find_group(groups,w):
    for gi,(gs,ge) in enumerate(groups):
        if gs<=w<=ge: return gi
    return None
d=open('extracted/packdata_raw/1197_type02.raw','rb').read()
sec1,sec2=load_sec(d); groups,words,_=parse_groups(sec2)
ok,instrs=walk(sec1); recs=extract_records(sec1,instrs)
# 0x04 at pc 0x91CD displays g904-912. Print the instruction stream from a bit
# before to a bit after, with opcodes, to see op21/op22/op14/op0C around it.
items=sorted(instrs.items())
# find index window around 0x91CD
lo=0x91CD-0x80; hi=0x91CD+0x10
def beu16(o): return struct.unpack_from('>H',sec1,o)[0]
def beu32(o): return struct.unpack_from('>I',sec1,o)[0]
print("Section-1 stream around Barkeep 0x04 (pc 0x91CD):")
for pc,op in items:
    if lo<=pc<=hi:
        extra=''
        if op==0x04: extra=f' DISPLAY off={beu32(pc+2)} cnt={beu32(pc+6)}'
        elif op==0x14: extra=f' LABEL off={beu32(pc+6)} cnt={beu32(pc+10)} g={find_group(groups,beu32(pc+6))}'
        elif op in (0x0C,0x0D): extra=f' NAMEREF param={beu16(pc+2)} idx={beu16(pc+4)}'
        elif op==0x21: extra=' <<SET box/dialogue mode (op21)'
        elif op==0x22: extra=' <<CLEAR box mode (op22)'
        print(f"  0x{pc:04X}: op 0x{op:02X}{extra}")
# Also: is there a name-island in g903? show 0x14 targeting 900-913
print("\n0x14 labels targeting groups 900-915:")
for r in recs['label']:
    g=find_group(groups,r['off'])
    if g is not None and 900<=g<=915:
        print(f"  pc=0x{r['pc']:X} -> g{g} off={r['off']} cnt={r['cnt']}")
