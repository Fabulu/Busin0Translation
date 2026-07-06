import sys, os, struct, json, glob
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('tools'))
from sec1_disasm import walk, extract_records
GM=json.load(open('data/msg_glyph_map.json',encoding='utf-8'))
HEADER_SIZE=0x20; CLOSE=61; OPEN=59
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

# The ~440 overflow victims are LONG dialogue blocks in the English. We approximate
# 'long dialogue block' as a DISPLAY block whose JP wraps to many lines (many FFFE)
# OR that the JP already paginated (FFD2). The question: of blocks that NEED pagination,
# what fraction does glyph-61 catch? And what fraction of NON-dialogue (narration) blocks
# does glyph-61 wrongly catch (must be 0)?
# Metric per block: n_fffe (line breaks), has_ffd2, has61, has_open59, name_island_in_block.
blocks=[]
for f in sorted(glob.glob('extracted/packdata_raw/*_type02.raw')):
    rid=int(os.path.basename(f).split('_')[0])
    d=open(f,'rb').read()
    try: sec1,sec2=load_sec(d)
    except: continue
    groups,words,_=parse_groups(sec2)
    if not groups: continue
    ok,instrs=walk(sec1); recs=extract_records(sec1,instrs)
    nameg=set(find_group(groups,r['off']) for r in recs['label']); nameg.discard(None)
    for r in recs['display']:
        if r['cnt']==0: continue
        gi0=find_group(groups,r['off'])
        if gi0 is None: continue
        gi1=find_group(groups,min(r['off']+r['cnt']-1,groups[-1][1])) or gi0
        gl=list(range(gi0,gi1+1))
        seg=[]
        for gi in gl:
            gs,ge=groups[gi]; seg+=list(words[gs:ge])
        nf=seg.count(0xFFFE); pf=seg.count(0xFFD2)
        h61=CLOSE in seg; h59=OPEN in seg
        ni=any(g in nameg for g in gl)
        blocks.append(dict(rid=rid,gl=gl,nf=nf,pf=pf,h61=h61,h59=h59,ni=ni))

# DIALOGUE ground-truth proxy = h61 OR ni (name island in block).  NARRATION proxy = not(h61 or ni).
dlg=[b for b in blocks if b['h61'] or b['ni']]
narr=[b for b in blocks if not (b['h61'] or b['ni'])]
# Of NARRATION-proxy blocks, how many have glyph61? (should be ~0 by def). And how many
# narration blocks have FFD2 (genuinely paginated narration -> the danger)?
narr_ffd2=[b for b in narr if b['pf']>0]
print(f"total DISPLAY blocks: {len(blocks)}")
print(f"DIALOGUE-proxy (h61 or name-island): {len(dlg)}")
print(f"NARRATION-proxy: {len(narr)}")
print(f"NARRATION-proxy blocks with glyph-61 (FP of glyph-61 signal): {sum(1 for b in narr if b['h61'])}")
print(f"NARRATION-proxy blocks with FFD2 (genuinely paginated narration): {len(narr_ffd2)}")
for b in narr_ffd2[:15]:
    print(f"   R{b['rid']} g{b['gl']} nf={b['nf']} pf={b['pf']} h59={b['h59']}")
# Coverage of glyph-61 over dialogue blocks
d61=sum(1 for b in dlg if b['h61'])
dni_only=sum(1 for b in dlg if (b['ni'] and not b['h61']))
print()
print(f"DIALOGUE blocks caught by glyph-61: {d61}/{len(dlg)} ({100*d61/len(dlg):.1f}%)")
print(f"DIALOGUE blocks caught ONLY by name-island (61 absent, e.g. Barkeep): {dni_only}")
# Among long blocks (nf>=4 => >=5 lines, likely overflow), glyph-61 coverage:
longb=[b for b in blocks if (b['nf']+2*b['pf'])>=4]  # rough line proxy
long_dlg=[b for b in longb if b['h61'] or b['ni']]
long_61=[b for b in long_dlg if b['h61']]
print()
print(f"LONG blocks (>=~5 lines): {len(longb)}; of those dialogue: {len(long_dlg)}; caught by glyph-61: {len(long_61)} ({100*len(long_61)/max(1,len(long_dlg)):.1f}%)")
