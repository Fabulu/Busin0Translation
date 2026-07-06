import sys, os, struct, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('tools'))
opt=json.load(open('build/recon_v85/exe-interpreter/opcode_table_v85.json'))
meta=opt['_meta']; ops=opt['opcodes']
LEN={int(k,16):v['bytes'] for k,v in ops.items()}
N_OPS=193
# control-flow opcode sets (mirror sec1_disasm)
import importlib.util
spec=importlib.util.spec_from_file_location('sd','tools/sec1_disasm.py')
sd=importlib.util.module_from_spec(spec); spec.loader.exec_module(sd)
JUMP_OPS=sd.JUMP_OPS; GOSUB_OPS=sd.GOSUB_OPS; COND_OPS=sd.COND_OPS; LENB=sd.LENB
HEADER_SIZE=0x20
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

def beu16(b,o): return struct.unpack_from('>H',b,o)[0]
def beu32(b,o): return struct.unpack_from('>I',b,o)[0]

def mode_walk(sec1):
    """BFS carrying mode bit (0=narr,1=dialogue). Returns {pc: set_of_modes_seen}."""
    n=len(sec1)
    seen={}  # pc -> set(modes)
    work=[(0,0)]
    conflicts=0
    while work:
        pc,mode=work.pop()
        while True:
            if pc<0 or pc+2>n: break
            if pc in seen and mode in seen[pc]: break
            seen.setdefault(pc,set()).add(mode)
            op=beu16(sec1,pc)
            if op>=N_OPS: break
            ln=LENB[op]
            nmode=mode
            if op==0x21: nmode=1
            elif op==0x22: nmode=0
            if op in JUMP_OPS:
                if pc+6>n: break
                t=beu32(sec1,pc+2)
                if t>=n: break
                pc=t; mode=nmode; continue
            if op in GOSUB_OPS:
                if pc+6<=n:
                    t=beu32(sec1,pc+2)
                    if t<n: work.append((t,nmode))
            if op in COND_OPS:
                if pc+14<=n:
                    t=beu32(sec1,pc+10)
                    if t<n: work.append((t,nmode))
            pc+=ln; mode=nmode
    return seen

def classify(rid):
    f=f'extracted/packdata_raw/{rid:04d}_type02.raw'
    d=open(f,'rb').read(); sec1,sec2=load_sec(d)
    groups,words,trailing=parse_groups(sec2)
    seen=mode_walk(sec1)
    # for each 0x04, get the mode at its pc
    g_mode={}  # group -> set of modes from all 0x04 referencing it
    n=len(sec1)
    pc=0
    # iterate all reachable pcs that are 0x04
    for pc,modes in seen.items():
        if pc+10>n: continue
        if beu16(sec1,pc)!=0x04: continue
        off=beu32(sec1,pc+2); cnt=beu32(sec1,pc+6)
        if cnt==0: continue
        gi0=find_group(groups,off); 
        if gi0 is None: continue
        gi1=find_group(groups,min(off+cnt-1,groups[-1][1])) or gi0
        for gi in range(gi0,gi1+1):
            g_mode.setdefault(gi,set()).update(modes)
    return groups,words,g_mode

# Stats: for each group with JP FFD2, what mode? for each narration group, mode?
import glob
from collections import Counter
TOTAL=Counter()
amb=0; ffd2_dlg=0; ffd2_narr=0; ffd2_amb=0; ffd2_none=0
narr_with_ffd2_examples=[]
for f in sorted(glob.glob('extracted/packdata_raw/*_type02.raw')):
    rid=int(os.path.basename(f).split('_')[0])
    try:
        groups,words,g_mode=classify(rid)
    except Exception as e:
        continue
    for gi,(gs,ge) in enumerate(groups):
        seg=words[gs:ge]
        if 0xFFD2 not in seg: continue
        m=g_mode.get(gi)
        if m is None: ffd2_none+=1
        elif m=={1}: ffd2_dlg+=1
        elif m=={0}: 
            ffd2_narr+=1
            if len(narr_with_ffd2_examples)<20: narr_with_ffd2_examples.append((rid,gi))
        else: ffd2_amb+=1
print("Groups containing JP 0xFFD2, classified by op21/op22 BFS mode:")
print(f"  mode=DIALOGUE only : {ffd2_dlg}")
print(f"  mode=NARRATION only: {ffd2_narr}   <-- these would be the dangerous narration-with-FFD2")
print(f"  mode=AMBIGUOUS(both): {ffd2_amb}")
print(f"  not reached by 0x04: {ffd2_none}")
print(f"  narration-mode FFD2 examples: {narr_with_ffd2_examples}")
