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
    name_groups=set(find_group(groups,r['off']) for r in recs['label'])
    name_groups.discard(None)
    # Walk Section-1 in pc/stream order. Track a 'dialogue-run' flag that is SET
    # when we pass a 0x14 name-island label and CLEARED when we hit a DISPLAY block
    # that contains NO close-61 AND whose first group is NOT contiguous with the
    # name run... no -- simpler and matched to runtime:
    # The box renderer is controlled by op 0x21(SET +0x290 bit0)/op 0x22(CLEAR).
    # Combine BOTH proven facts: (1) op21..op22 stream bracket; (2) glyph-61.
    items=sorted(instrs.items())
    def beu32(o): return struct.unpack_from('>I',sec1,o)[0]
    box=False
    dlg_groups=set(); narr_groups=set()
    for pc,op in items:
        if op==0x21: box=True
        elif op==0x22: box=False
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
            is_dlg = box or (CLOSE in seg)
            for gi in gl:
                (dlg_groups if is_dlg else narr_groups).add(gi)
    return groups,words,dlg_groups,narr_groups,name_groups

for rid,exp_dlg,exp_narr in [(1197,[903,904,905,906,907,912],[]),
                              (1196,[574],[567,568,569,575,576,577,578])]:
    groups,words,dlg,narr,nm=classify(rid)
    print(f"=== R{rid} ===")
    for g in exp_dlg: print(f"  g{g}: {'DIALOGUE' if g in dlg else 'NARRATION' if g in narr else 'NEITHER'}")
    for g in exp_narr: print(f"  g{g}: {'DIALOGUE' if g in dlg else 'NARRATION' if g in narr else 'NEITHER'}")

# Audit: JP FFD2 groups should all be dialogue; narration FFD2-FP impossible.
ffd2_dlg=ffd2_narr=ffd2_un=ffd2_total=0
# Also key safety metric: of groups classified NARRATION, how many would we touch? none.
for f in sorted(glob.glob('extracted/packdata_raw/*_type02.raw')):
    rid=int(os.path.basename(f).split('_')[0])
    try: groups,words,dlg,narr,nm=classify(rid)
    except: continue
    for gi,(gs,ge) in enumerate(groups):
        if 0xFFD2 in words[gs:ge]:
            ffd2_total+=1
            if gi in dlg: ffd2_dlg+=1
            elif gi in narr: ffd2_narr+=1
            else: ffd2_un+=1
print()
print(f"JP FFD2 groups={ffd2_total}: DIALOGUE={ffd2_dlg} NARRATION={ffd2_narr} unreached={ffd2_un}")
