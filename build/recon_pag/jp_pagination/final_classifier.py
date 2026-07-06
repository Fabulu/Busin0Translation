import sys, os, struct, json, glob
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('tools'))
from sec1_disasm import walk, extract_records
GM=json.load(open('data/msg_glyph_map.json',encoding='utf-8'))
HEADER_SIZE=0x20; OPEN=59; CLOSE=61
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

# DEFINE the block-level dialogue classifier:
#   A 0x04 DISPLAY_TEXT block is DIALOGUE iff its concatenated glyph stream contains
#   the dialogue-close glyph 61 (ゴ).  (Equivalently opens with 59 somewhere.)
# We then need to know, for the ENGLISH build, which GROUPS belong to dialogue blocks
# so we can auto-paginate ONLY those groups.

def classify_resource(rid):
    f=f'extracted/packdata_raw/{rid:04d}_type02.raw'
    d=open(f,'rb').read(); sec1,sec2=load_sec(d)
    groups,words,_=parse_groups(sec2)
    ok,instrs=walk(sec1); recs=extract_records(sec1,instrs)
    dlg_groups=set(); narr_groups=set()
    for r in recs['display']:
        if r['cnt']==0: continue
        gi0=find_group(groups,r['off'])
        if gi0 is None: continue
        gi1=find_group(groups,min(r['off']+r['cnt']-1,groups[-1][1])) or gi0
        gl=list(range(gi0,gi1+1))
        seg=[]
        for gi in gl:
            gs,ge=groups[gi]; seg+=list(words[gs:ge])
        is_dlg = CLOSE in seg
        for gi in gl:
            (dlg_groups if is_dlg else narr_groups).add(gi)
    return groups,words,dlg_groups,narr_groups

# Confirm specific cases
for rid,gs_dlg,gs_narr in [(1197,[904,905,906,907],[]),(1196,[574],[567,568,569,575,576,577,578])]:
    groups,words,dlg,narr=classify_resource(rid)
    print(f"=== R{rid} ===")
    for g in gs_dlg:
        print(f"  g{g}: classified={'DIALOGUE' if g in dlg else 'NARRATION' if g in narr else 'NEITHER'} (expect DIALOGUE)")
    for g in gs_narr:
        print(f"  g{g}: classified={'DIALOGUE' if g in dlg else 'NARRATION' if g in narr else 'NEITHER'} (expect NARRATION)")

# Global false-positive audit: any group that is BOTH in a dialogue block and a
# narration block (ambiguous)?  And total tallies.
tot_dlg=0; tot_narr=0; ambiguous=0
for f in sorted(glob.glob('extracted/packdata_raw/*_type02.raw')):
    rid=int(os.path.basename(f).split('_')[0])
    try: groups,words,dlg,narr=classify_resource(rid)
    except: continue
    amb=dlg & narr
    ambiguous+=len(amb)
    tot_dlg+=len(dlg-narr); tot_narr+=len(narr-dlg)
print()
print(f"GLOBAL: dialogue-only groups={tot_dlg}, narration-only groups={tot_narr}, AMBIGUOUS(both)={ambiguous}")
