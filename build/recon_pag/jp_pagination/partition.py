import sys, os, struct, json, glob
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('tools'))
from sec1_disasm import walk, extract_records
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

# Hypothesis tests per GROUP that contains FFD2 (page break):
#  T1: group contains an inline name marker 0xFFE0..0xFFE7
#  T2: group's first non-control glyph == 59 (dialogue-open) OR contains 59
#  T3: group contains the closing 61 (ゴ)
# And per group WITHOUT ffd2 that IS narration-like.
# GOAL: find a per-group predicate P such that:
#   every group that has FFD2 (JP dialogue) -> P true
#   no narration group -> P true
# Test on all type02.

def is_ctrl(w): return w>=0xFB00
def first_text_glyph(seg):
    for w in seg:
        if not is_ctrl(w): return w
    return None

files=sorted(glob.glob('extracted/packdata_raw/*_type02.raw'))
# Collect groups
all_g=[]  # (rid,gi,has_ffd2,has_namemark,starts59,has59,has61)
for f in files:
    rid=int(os.path.basename(f).split('_')[0])
    d=open(f,'rb').read()
    try: sec1,sec2=load_sec(d)
    except: continue
    groups,words,trailing=parse_groups(sec2)
    for gi,(gs,ge) in enumerate(groups):
        seg=words[gs:ge]
        if not seg: continue
        has_ffd2=0xFFD2 in seg
        has_nm=any(0xFFE0<=w<=0xFFE7 for w in seg)
        f59 = (first_text_glyph(seg)==59)
        h59 = 59 in seg
        h61 = 61 in seg
        all_g.append((rid,gi,has_ffd2,has_nm,f59,h59,h61))

ffd2_groups=[g for g in all_g if g[2]]
print(f"total groups: {len(all_g)}; groups with FFD2: {len(ffd2_groups)}")
# How many FFD2 groups satisfy each predicate?
def frac(pred, subset):
    n=sum(1 for g in subset if pred(g)); return n,len(subset)
for name,pred in [
    ('namemark',  lambda g:g[3]),
    ('startsglyph59', lambda g:g[4]),
    ('has59', lambda g:g[5]),
    ('has61', lambda g:g[6]),
    ('namemark OR starts59', lambda g:g[3] or g[4]),
    ('namemark OR has59', lambda g:g[3] or g[5]),
    ('has59 AND has61', lambda g:g[5] and g[6]),
    ('namemark OR (has59 AND has61)', lambda g:g[3] or (g[5] and g[6])),
]:
    n,t=frac(pred,ffd2_groups)
    print(f"  FFD2-groups satisfying [{name}]: {n}/{t}  ({100*n/t:.1f}%)")

# Now: among NON-ffd2 groups, how many would a candidate predicate FALSE-POSITIVE on?
# We care: a narration group must be predicate-FALSE. We approximate 'narration' as
# non-ffd2 groups WITHOUT name markers and WITHOUT glyph59-start.
print()
nonf=[g for g in all_g if not g[2]]
print(f"non-FFD2 groups: {len(nonf)}")
for name,pred in [
    ('namemark',  lambda g:g[3]),
    ('startsglyph59', lambda g:g[4]),
    ('namemark OR starts59', lambda g:g[3] or g[4]),
    ('namemark OR (has59 AND has61)', lambda g:g[3] or (g[5] and g[6])),
]:
    n,t=frac(pred,nonf)
    print(f"  non-FFD2 groups satisfying [{name}] (would be flagged dialogue): {n}/{t} ({100*n/t:.1f}%)")
