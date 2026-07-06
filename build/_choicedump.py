import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tests')
from _helpers import parse_type02, group_offsets
def load(p):
    d=open(p,'rb').read(); w=parse_type02(d)['words']; offs,_=group_offsets(w); return w,offs
def grp(w,offs,gi):
    s,e=offs[gi]; return w[s:e]
def fmt(g):
    out=[]
    for x in g:
        if x==0xFFFE: out.append('|FFFE|')
        elif x==0xFFFF: out.append('|FFFF|')
        elif x==0xFFD2: out.append('|FFD2|')
        elif 0xFFC0<=x<=0xFFCF: out.append('<<FFC%d>>'%(x-0xFFC0))
        elif x>=0xFB00: out.append('{%04X}'%x)
        else: out.append('g')
    return ' '.join(out)
gi=int(sys.argv[1])
wo,oo=load('extracted/packdata_raw/1197_type02.raw')
wb,ob=load('build/patched_type2/1197_type02.raw')
print('PRISTINE g%d:'%gi); print(' ',fmt(grp(wo,oo,gi)))
print('BUILT    g%d:'%gi); print(' ',fmt(grp(wb,ob,gi)))
