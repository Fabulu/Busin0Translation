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

# For a resource, walk Section-1 in STREAM order tracking the +0x290 bit0 mode set
# by op 0x21 (SET) and op 0x22 (CLEAR). For each 0x04 DISPLAY_TEXT, record the mode.
# NOTE: 'stream order' is the natural pc order of the linear scan; the runtime is
# control-flow ordered, but op21/op22 SET/CLEAR are typically lexically bracketed.
def analyze(rid, want_groups):
    f=f'extracted/packdata_raw/{rid:04d}_type02.raw'
    d=open(f,'rb').read(); sec1,sec2=load_sec(d)
    groups,words,trailing=parse_groups(sec2)
    ok,instrs=walk(sec1)
    # linear scan in pc order, tracking mode
    items=sorted(instrs.items())
    mode=0  # 0=narration, 1=dialogue
    res={}
    for pc,op in items:
        if op==0x21: mode=1
        elif op==0x22: mode=0
        elif op==0x04:
            off=struct.unpack_from('>I',sec1,pc+2)[0]
            cnt=struct.unpack_from('>I',sec1,pc+6)[0]
            if cnt==0: continue
            gi=find_group(groups,off)
            if gi is None: continue
            res[gi]=mode
    for g in want_groups:
        gs,ge=groups[g]; seg=words[gs:ge]
        hf=0xFFD2 in seg
        print(f"  R{rid} g{g}: mode={res.get(g,'?')} ({'DIALOGUE' if res.get(g)==1 else 'NARRATION' if res.get(g)==0 else '?'})  JP_has_FFD2={hf}")

print("=== KNOWN DIALOGUE: R1197 Barkeep (g903 name, g905 long) ===")
analyze(1197,[903,904,905,906,907])
print("=== KNOWN NARRATION: R1196 intro (g567-578, g574 is embedded dialogue) ===")
analyze(1196,[567,568,569,574,575,576,577])
