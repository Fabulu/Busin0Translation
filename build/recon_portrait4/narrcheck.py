import sys, json, glob, struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools')
from patch_section1_offsets import walk, extract_records, _bucket_labels, HEADER_SIZE
RAW='extracted/packdata_raw'
def _wrap_line(seg,mx):
    out=[]
    while len(seg)>mx:
        b=seg.rfind(' ',0,mx+1)
        if b<=0: b=mx
        out.append(seg[:b]); seg=seg[b:].lstrip(' ')
    out.append(seg); return out
def wrap(text,mx):
    return ' // '.join(' / '.join(l for seg in pg.split(' / ') for l in _wrap_line(seg,mx)) for pg in text.split(' // '))
all_trans={}
for fn in sorted(glob.glob('data/type2_translated/batch_*.json')):
    for e in json.load(open(fn,encoding='utf-8')):
        if 'msg_index' in e:
            all_trans.setdefault(e['resource'],{})[e['msg_index']]=e.get('english','')
# For R1196 (has narration), compare: at w=19, how many narration lines exceed,
# the worst-case line length when allowing 19? max produced line is <=19 by definition
# since _wrap_line guarantees <=mx unless a single token > mx.
# So the real question: single tokens > 19 that force-break ugly. Count tokens >16 and >19.
import collections
longtok=collections.Counter()
worst=[]
for res in all_trans:
    for mi,t in all_trans[res].items():
        if not t or any(ord(c)>127 for c in t): continue
        for tok in t.replace(' / ',' ').replace(' // ',' ').split():
            tok=tok.replace('\n',' ')
            for w in tok.split():
                if len(w)>16:
                    longtok[len(w)]+=1
                    if len(w)>19 and len(worst)<15: worst.append((res,mi,w))
print("single tokens (words) longer than 16 chars -> these force-break at ANY width:")
print(sorted(longtok.items()))
print("tokens >19:")
for r,m,w in worst: print(f"  R{r} g{m}: {w!r}")
