import sys, struct, os, glob, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools'); sys.path.insert(0,'build/recon_pag')
sys.path.insert(0,'build')
from spans import load, groups_in_span

# Reproduce build wrap (TYPE2_WRAP_WIDTH=19)
W=19
def _wrap_line(seg,m=W):
    out=[]
    while len(seg)>m:
        brk=seg.rfind(' ',0,m+1)
        if brk<=0: brk=m
        out.append(seg[:brk]); seg=seg[brk:].lstrip(' ')
    out.append(seg); return out
def wrap(text):
    pages=[]
    for page in text.split(' // '):
        lines=[]
        for seg in page.split(' / '): lines.extend(_wrap_line(seg))
        pages.append(' / '.join(lines))
    return ' // '.join(pages)
def lines_on_worst_page(text):
    w=wrap(text)
    return max(len(p.split(' / ')) for p in w.split(' // '))

# Load all english type2 translations
trans={}  # (res,mi)->text
for fn in glob.glob('data/type2_translated/batch_*.json'):
    try: d=json.load(open(fn,encoding='utf-8'))
    except: continue
    for e in d:
        if 'msg_index' not in e or 'resource' not in e: continue
        trans[(e['resource'],e['msg_index'])]=e.get('english') or ''
# message index = group index (0-indexed FFFF groups), per build pipeline
print("loaded %d english translations"%len(trans))
# count overflowing translations (>4 lines on a single page, no existing //)
overflow=[]
for (res,mi),txt in trans.items():
    if not txt: continue
    if ' // ' in txt: continue  # already authored a page break
    n=lines_on_worst_page(txt)
    if n>4:
        overflow.append((res,mi,n,txt))
overflow.sort(key=lambda x:-x[2])
print("OVERFLOWING english translations (>4 lines, no authored //): %d"%len(overflow))
from collections import Counter
byres=Counter(o[0] for o in overflow)
print("top resources:", byres.most_common(15))
print("worst 15:")
for res,mi,n,txt in overflow[:15]:
    print("  R%d g%d: %d lines | %s"%(res,mi,n,(txt[:60]+'...') if len(txt)>60 else txt))
# save
json.dump([{'resource':r,'message':m,'lines':n,'text':t} for r,m,n,t in overflow],
          open('build/recon_pag/overflow_worklist.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
