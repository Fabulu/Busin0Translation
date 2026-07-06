import sys, os, struct, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('tools'))
from sec1_disasm import walk, extract_records
HEADER_SIZE=0x20
LENB=None
# Load opcode lengths
opt=json.load(open('build/recon_v85/exe-interpreter/opcode_table_v85.json'))
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

# For R1196 (mixed narration+dialogue), list EVERY 0x04 DISPLAY_TEXT in Section-1 ORDER,
# with: the opcodes in a window BEFORE the 0x04, whether the target group has FFD2,
# whether it has a name marker. Look for an opcode that flips between narr & dialogue.
def beu16(b,o): return struct.unpack_from('>H',b,o)[0]
rid=1196
f=f'extracted/packdata_raw/{rid:04d}_type02.raw'
d=open(f,'rb').read(); sec1,sec2=load_sec(d)
groups,words,trailing=parse_groups(sec2)
ok,instrs=walk(sec1); recs=extract_records(sec1,instrs)
# Build sorted instr list
ilist=sorted(instrs.items())
pc2idx={pc:i for i,(pc,op) in enumerate(ilist)}
# For each 0x04, find the 6 opcodes preceding it in stream order
def has_nm(gi):
    gs,ge=groups[gi]; return any(0xFFE0<=w<=0xFFE7 for w in words[gs:ge])
def has_ffd2(gi):
    gs,ge=groups[gi]; return 0xFFD2 in words[gs:ge]
print("R1196 DISPLAY_TEXT in stream order (op-before chain | tgt group | NM | FFD2):")
for r in recs['display']:
    if r['cnt']==0: continue
    pc=r['pc']; idx=pc2idx.get(pc)
    if idx is None: continue
    prev=[f'{ilist[j][1]:02X}' for j in range(max(0,idx-6),idx)]
    gi=find_group(groups,r['off'])
    if gi is None: continue
    nm='NM' if has_nm(gi) else '  '
    fd='FFD2' if has_ffd2(gi) else '    '
    print(f"  pc=0x{pc:04X} g{gi:4d} {nm} {fd} prev=[{' '.join(prev)}]")
