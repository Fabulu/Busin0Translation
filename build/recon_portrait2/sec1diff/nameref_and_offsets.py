import struct, sys, os, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools')
import sec1_disasm as S
SECTOR=2048; N=2883
def find_packdata(iso):
    with open(iso,'rb') as f:
        f.seek(16*SECTOR); pvd=f.read(SECTOR)
        rl=struct.unpack_from('<I',pvd,158)[0]; rs=struct.unpack_from('<I',pvd,166)[0]
        f.seek(rl*SECTOR); root=f.read(rs); pos=0
        while pos<len(root):
            L=root[pos]
            if L==0: break
            nl=root[pos+32]; name=root[pos+33:pos+33+nl].decode('latin1','ignore')
            if 'PACKDATA' in name: return struct.unpack_from('<I',root,pos+2)[0], struct.unpack_from('<I',root,pos+10)[0]
            pos+=L
def toc(iso):
    lba,_=find_packdata(iso)
    with open(iso,'rb') as f:
        f.seek(lba*SECTOR); return lba,[struct.unpack('<III',f.read(12)) for _ in range(N)]
def res(iso,lba,t,i):
    so,sc,tc=t[i]
    with open(iso,'rb') as f:
        f.seek((lba+so)*SECTOR); return f.read(sc*SECTOR)
JP='Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso'
V90='build/BUSIN0_EN_v90.iso'
jl,jt=toc(JP); vl,vt=toc(V90)

for RES in [1196,1197]:
    a=res(JP,jl,jt,RES); b=res(V90,vl,vt,RES)
    sa=struct.unpack_from('<I',a,0x18)[0]; sb=struct.unpack_from('<I',b,0x18)[0]
    s1a=a[0x20:sa]; s1b=b[0x20:sb]
    oka,ia=S.walk(s1a); okb,ib=S.walk(s1b)
    ra=S.extract_records(s1a,ia); rb=S.extract_records(s1b,ib)
    print(f'\n=== R{RES} ===')
    # 0x0C/0x0D nameref: compare param AND idx
    na=ra['name_ref']; nb=rb['name_ref']
    print(f'  name_ref count JP={len(na)} V90={len(nb)}')
    param_mismatch=0; idx_mismatch=0; idx_match=0
    for x,y in zip(na,nb):
        assert x['pc']==y['pc']
        if x['param']!=y['param']: param_mismatch+=1; print(f'    PARAM MISMATCH pc=0x{x["pc"]:x} JP param={x["param"]} idx={x["idx"]} | V90 param={y["param"]} idx={y["idx"]}')
        if x['idx']!=y['idx']: idx_mismatch+=1
        else: idx_match+=1
    print(f'  0x0C/0x0D: param mismatches={param_mismatch}  idx mismatches={idx_mismatch}  idx identical={idx_match}')

    # 0x04 DISPLAY_TEXT: verify off remapped monotonically (cnt may grow)
    da=ra['display']; db=rb['display']
    print(f'  0x04 DISPLAY_TEXT count JP={len(da)} V90={len(db)}')
    # check: is V90 off always >= JP off (text grew, offsets shift up)? and is mapping monotone & consistent?
    off_changed=sum(1 for x,y in zip(da,db) if x['off']!=y['off'])
    cnt_changed=sum(1 for x,y in zip(da,db) if x['cnt']!=y['cnt'])
    neg=sum(1 for x,y in zip(da,db) if y['off']<x['off'])
    print(f'    off changed={off_changed} cnt changed={cnt_changed} V90off<JPoff (suspicious)={neg}')
    # 0x14
    la=ra['label']; lb=rb['label']
    print(f'  0x14 LABEL count JP={len(la)} V90={len(lb)}')
    lpm=sum(1 for x,y in zip(la,lb) if x['param']!=y['param'])
    loff=sum(1 for x,y in zip(la,lb) if x['off']!=y['off'])
    lcnt=sum(1 for x,y in zip(la,lb) if x['cnt']!=y['cnt'])
    lneg=sum(1 for x,y in zip(la,lb) if y['off']<x['off'])
    print(f'    param changed={lpm} off changed={loff} cnt changed={lcnt} V90off<JPoff={lneg}')
