import sys, json, glob, collections
sys.stdout.reconfigure(encoding='utf-8')
all_trans={}
for fn in sorted(glob.glob('data/type2_translated/batch_*.json')):
    try:
        for e in json.load(open(fn,encoding='utf-8')):
            if 'msg_index' not in e: continue
            all_trans.setdefault(e['resource'],{})[e['msg_index']]=e.get('english','')
    except Exception as ex:
        print('skip',fn,ex)
hist=collections.Counter(); o16=o18=o19=total=0; ex=[]
for res in all_trans:
    for mi,t in all_trans[res].items():
        if not t or any(ord(c)>127 for c in t): continue
        for page in t.split(' // '):
            for seg in page.split(' / '):
                L=len(seg); hist[L]+=1; total+=1
                if L>16: o16+=1
                if L>18: o18+=1
                if L>19:
                    o19+=1
                    if len(ex)<10: ex.append((res,mi,L,seg))
print(f"total authored segments={total}")
print(f"  >16: {o16} ({100*o16/total:.1f}%)  >18: {o18} ({100*o18/total:.1f}%)  >19: {o19} ({100*o19/total:.1f}%)")
print("examples >19:")
for r,m,L,s in ex: print(f"  R{r} g{m} len={L}: {s!r}")
