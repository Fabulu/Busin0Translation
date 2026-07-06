import sys, json, glob
sys.stdout.reconfigure(encoding='utf-8')
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
# R1203 total words (chars + breaks) at w=16 vs w=19, groups<=1016
def total_words(res,mx,cap=None):
    tot=0
    for mi,t in all_trans[res].items():
        if cap is not None and mi>cap: continue
        if not t or any(ord(c)>127 for c in t): continue
        w=wrap(t,mx)
        words=0
        for pi,pg in enumerate(w.split(' // ')):
            if pi>0: words+=1
            for li,ln in enumerate(pg.split(' / ')):
                if li>0: words+=1
                words+=len(ln)
        tot+=words
    return tot
print("R1203 translated-text word totals (lower=safer for cap):")
print("  w=16:",total_words(1203,16,1016))
print("  w=19:",total_words(1203,19,1016))
