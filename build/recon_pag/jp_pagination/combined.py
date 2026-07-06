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
    name_groups=set()
    for r in recs['label']:
        g=find_group(groups,r['off'])
        if g is not None: name_groups.add(g)
    # DISPLAY blocks sorted by pc (Section-1 stream order)
    disp=sorted([(r['pc'],r['off'],r['cnt']) for r in recs['display'] if r['cnt']>0])
    # Build block group-lists
    blocks=[]
    for pc,off,cnt in disp:
        gi0=find_group(groups,off)
        if gi0 is None: continue
        gi1=find_group(groups,min(off+cnt-1,groups[-1][1])) or gi0
        gl=list(range(gi0,gi1+1))
        seg=[]
        for gi in gl:
            gs,ge=groups[gi]; seg+=list(words[gs:ge])
        blocks.append((pc,gl,seg))
    # signal A: contains close glyph 61
    # signal B: block starts at, or immediately follows in group-order, a name-island group.
    #   A name-labeled dialogue "utterance" = the name group + its following continuation
    #   groups, up to the next name group or a narration block. We mark a block dialogue
    #   if its first group is a name group OR its first group == (prev dialogue block last
    #   group + 1) chained from a name-island start.
    dlg_groups=set(); narr_groups=set()
    # First pass: signal A
    blockflag={}
    for i,(pc,gl,seg) in enumerate(blocks):
        a = CLOSE in seg
        b_start = gl[0] in name_groups
        blockflag[i]=dict(gl=gl, a=a, bstart=b_start)
    # Second pass: propagate name-island dialogue across contiguous group runs.
    # Sort blocks by first group.
    order=sorted(range(len(blocks)), key=lambda i: blockflag[i]['gl'][0])
    active=False; last_g=-99
    for i in order:
        gl=blockflag[i]['gl']
        if blockflag[i]['bstart']:
            active=True
        elif gl[0] != last_g+1:
            # gap in group sequence -> dialogue run ends unless this block is itself dialogue-A
            active=False
        is_dlg = blockflag[i]['a'] or active
        for g in gl:
            (dlg_groups if is_dlg else narr_groups).add(g)
        last_g=gl[-1]
    return groups,words,dlg_groups,narr_groups,name_groups

# Validate known cases
for rid,exp_dlg,exp_narr in [(1197,[903,904,905,906,907,912],[]),
                              (1196,[574],[567,568,569,575,576,577,578])]:
    groups,words,dlg,narr,nm=classify(rid)
    print(f"=== R{rid} ===")
    for g in exp_dlg: print(f"  g{g}: {'DIALOGUE' if g in dlg else 'NARRATION' if g in narr else 'NEITHER'} (expect DIALOGUE)")
    for g in exp_narr: print(f"  g{g}: {'DIALOGUE' if g in dlg else 'NARRATION' if g in narr else 'NEITHER'} (expect NARRATION)")

# FALSE-POSITIVE AUDIT: does the combined classifier ever flag a narration group?
# A narration group = a group with NO glyph-61 and NOT in a name-island run. We can't
# know ground truth perfectly, but we CAN check: of the 5936 'narration prose' blocks
# (no glyph 61, in earlier test), how many does the combined classifier now flag dialogue?
# Cross-check: every group that the JP itself paginated (has FFD2) — is it now DIALOGUE?
ffd2_dlg=0; ffd2_narr=0; ffd2_total=0
for f in sorted(glob.glob('extracted/packdata_raw/*_type02.raw')):
    rid=int(os.path.basename(f).split('_')[0])
    try: groups,words,dlg,narr,nm=classify(rid)
    except: continue
    for gi,(gs,ge) in enumerate(groups):
        if 0xFFD2 in words[gs:ge]:
            ffd2_total+=1
            if gi in dlg: ffd2_dlg+=1
            elif gi in narr: ffd2_narr+=1
print()
print(f"JP FFD2 groups total={ffd2_total}: classified DIALOGUE={ffd2_dlg}, NARRATION={ffd2_narr}, unreached={ffd2_total-ffd2_dlg-ffd2_narr}")
print("(Every JP-paginated group SHOULD be DIALOGUE; NARRATION here = false-negative that stays overflowing — but a NARRATION FFD2 group flagged DIALOGUE would be the dangerous case, which is impossible since these ARE dialogue.)")
