import sys, os, struct, json, glob
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('tools'))
from sec1_disasm import walk, extract_records
GM=json.load(open('data/msg_glyph_map.json',encoding='utf-8'))
HEADER_SIZE=0x20; CLOSE=61
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

def classify(rid):
    f=f'extracted/packdata_raw/{rid:04d}_type02.raw'
    d=open(f,'rb').read(); sec1,sec2=load_sec(d)
    groups,words,_=parse_groups(sec2)
    ok,instrs=walk(sec1); recs=extract_records(sec1,instrs)
    name_groups=set(find_group(groups,r['off']) for r in recs['label']); name_groups.discard(None)
    items=sorted(instrs.items())
    def beu32(o): return struct.unpack_from('>I',sec1,o)[0]
    dlg=set(); narr=set()
    # pc-stream pass: dialogue-run flag set when a 0x14 name-island is seen; it stays
    # active across IMMEDIATELY-FOLLOWING DISPLAY blocks that are group-contiguous;
    # any non-contiguous DISPLAY or a 0x22 clears it.  glyph-61 always forces dialogue.
    run=False; prev_last=None
    for pc,op in items:
        if op==0x14:
            g=find_group(groups,beu32(pc+6))
            if g is not None:
                run=True; prev_last=g  # name group becomes part of the run
        elif op==0x22:
            run=False; prev_last=None
        elif op==0x04:
            off=beu32(pc+2); cnt=beu32(pc+6)
            if cnt==0: continue
            gi0=find_group(groups,off)
            if gi0 is None: continue
            gi1=find_group(groups,min(off+cnt-1,groups[-1][1])) or gi0
            gl=list(range(gi0,gi1+1))
            seg=[]
            for gi in gl:
                gs,ge=groups[gi]; seg+=list(words[gs:ge])
            has61 = CLOSE in seg
            # is this DISPLAY contiguous with the active name run?
            contig = run and (prev_last is not None) and (gl[0]==prev_last+1 or gl[0]==prev_last)
            is_dlg = has61 or contig
            if is_dlg:
                for gi in gl: dlg.add(gi)
                if contig: prev_last=gl[-1]
                else: run=False; prev_last=None  # glyph-61 island doesn't extend a name run
            else:
                for gi in gl: narr.add(gi)
                run=False; prev_last=None
    return groups,words,dlg,narr

for rid,exp_dlg,exp_narr in [(1197,[903,904,905,906,907,912],[]),
                              (1196,[574],[567,568,569,575,576,577,578])]:
    groups,words,dlg,narr=classify(rid)
    print(f"=== R{rid} ===")
    for g in exp_dlg: print(f"  g{g}: {'DIALOGUE' if g in dlg else 'NARRATION' if g in narr else 'NEITHER'}")
    for g in exp_narr: print(f"  g{g}: {'DIALOGUE' if g in dlg else 'NARRATION' if g in narr else 'NEITHER'}")

# Safety audits
ffd2_dlg=ffd2_narr=ffd2_un=ffd2_total=0
narr_fp=[]   # narration groups wrongly flagged dialogue -> we approximate "narration" as
# groups that are reached, classified narration in the GLYPH-61-pure pass (true narration)
# Build glyph-61-pure narration set per resource to detect any new FP from the name-run.
for f in sorted(glob.glob('extracted/packdata_raw/*_type02.raw')):
    rid=int(os.path.basename(f).split('_')[0])
    try: groups,words,dlg,narr=classify(rid)
    except: continue
    for gi,(gs,ge) in enumerate(groups):
        if 0xFFD2 in words[gs:ge]:
            ffd2_total+=1
            if gi in dlg: ffd2_dlg+=1
            elif gi in narr: ffd2_narr+=1
            else: ffd2_un+=1
print()
print(f"JP FFD2 groups={ffd2_total}: DIALOGUE={ffd2_dlg} NARRATION={ffd2_narr} unreached={ffd2_un}")
