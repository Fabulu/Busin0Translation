import sys, json, glob
sys.stdout.reconfigure(encoding='utf-8')
def _wrap_line(seg,mx):
    out=[]
    while len(seg)>mx:
        b=seg.rfind(' ',0,mx+1)
        if b<=0: b=mx
        out.append(seg[:b]); seg=seg[b:].lstrip(' ')
    out.append(seg); return out
def lines_of(text,mx):
    res=[]
    for pg in text.split(' // '):
        for seg in pg.split(' / '):
            res.extend(_wrap_line(seg,mx))
    return res
all_trans={}
for fn in sorted(glob.glob('data/type2_translated/batch_*.json')):
    for e in json.load(open(fn,encoding='utf-8')):
        if 'msg_index' in e:
            all_trans.setdefault(e['resource'],{})[e['msg_index']]=e.get('english','')
# narration groups in R1196
for gi in [0,1,2,11,12,13,575]:
    t=all_trans[1196][gi]
    l16=lines_of(t,16); l19=lines_of(t,19)
    maxlen19=max(len(x) for x in l19)
    print(f"g{gi}: 16->{len(l16)}ln  19->{len(l19)}ln maxlen19={maxlen19}")
    print(f"    16: {l16}")
    print(f"    19: {l19}")
