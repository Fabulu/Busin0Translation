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
    pages=[]
    for pg in text.split(' // '):
        lines=[]
        for seg in pg.split(' / '):
            lines.extend(_wrap_line(seg,mx))
        pages.append(' / '.join(lines))
    return ' // '.join(pages)
all_trans={}
for fn in sorted(glob.glob('data/type2_translated/batch_*.json')):
    for e in json.load(open(fn,encoding='utf-8')):
        if 'msg_index' in e:
            all_trans.setdefault(e['resource'],{})[e['msg_index']]=e.get('english','')
targets=[(1196,577,'Shady NAME'),(1196,578,'Shady'),(1196,583,'Shady That\'s why'),(1196,602,'Sister'),(1197,925,'Lady Knight')]
for res,gi,desc in targets:
    t=all_trans[res][gi]
    print(f"=== R{res} g{gi} ({desc}) ===")
    print(f"  raw: {t!r}")
    for w in [16,18,19]:
        wrapped=wrap(t,w)
        lines=[]
        for pg in wrapped.split(' // '):
            lines.extend(pg.split(' / '))
        print(f"  w={w}: {len(lines)} lines: {[ (l,len(l)) for l in lines]}")
