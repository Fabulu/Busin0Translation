import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tests')
from _helpers import parse_type02, group_offsets
def load(p):
    d=open(p,'rb').read(); w=parse_type02(d)['words']; offs,_=group_offsets(w); return w,offs
def grp(w,offs,gi):
    s,e=offs[gi]; return w[s:e]
def marker_lines(g):
    # emulate render pass: s1=line index, FFFE increments s1 (capped 0x1f), FFCx flags line s1
    s1=0; lines=[]; optcount=0
    for x in g:
        if x==0xFFFE:
            if s1<0x1f: s1+=1
            optcount+=1
        elif 0xFFC0<=x<=0xFFCF:
            lines.append((x-0xFFC0, s1)); optcount+=1
    return lines, optcount
for src,p in (('PRISTINE','extracted/packdata_raw/1197_type02.raw'),('BUILT','build/patched_type2/1197_type02.raw')):
    w,offs=load(p)
    for gi in (652,916,63):
        ml,oc=marker_lines(grp(w,offs,gi))
        marked=[ln for _,ln in ml]
        collide = len(marked)!=len(set(marked))
        print('%-9s g%-4d  markers->lines=%s  distinct=%s  COLLISION=%s'%(src,gi,ml,not collide and 'ok',collide))
