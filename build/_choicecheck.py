import sys, struct, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tests')
from _helpers import parse_type02, group_offsets
def load(p):
    d=open(p,'rb').read()
    w=parse_type02(d)['words']
    offs,_=group_offsets(w)
    return w,offs
def grp(w,offs,gi):
    s,e=offs[gi]
    return w[s:e]
def summ(g):
    ffc=[hex(x) for x in g if 0xFFC0<=x<=0xFFCF]
    nfe=sum(1 for x in g if x==0xFFFE)
    nd2=sum(1 for x in g if x==0xFFD2)
    return 'len=%d FFCx=%s FFFE=%d FFD2=%d'%(len(g),ffc,nfe,nd2)
for gi in (652,916,63):
    try:
        wo,oo=load('extracted/packdata_raw/1197_type02.raw')
        wb,ob=load('build/patched_type2/1197_type02.raw')
        print('--- g%d ---'%gi)
        print('  pristine:',summ(grp(wo,oo,gi)))
        print('  built   :',summ(grp(wb,ob,gi)))
    except Exception as e:
        print('g%d err %s'%(gi,e))
