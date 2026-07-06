import struct, sys, json
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
tbl=json.load(open('build/recon_v85/exe-interpreter/opcode_table_v85.json',encoding='utf-8'))
opinfo={int(k,16):v for k,v in tbl['opcodes'].items()}

from collections import Counter
for RES in [1196,1197]:
    a=res(JP,jl,jt,RES); b=res(V90,vl,vt,RES)
    sa=struct.unpack_from('<I',a,0x18)[0]; sb=struct.unpack_from('<I',b,0x18)[0]
    s1a=a[0x20:sa]; s1b=b[0x20:sb]
    oka,ia=S.walk(s1a); okb,ib=S.walk(s1b)
    cnt=Counter(ia.values())
    print(f'\n=== R{RES} opcode census ({len(ia)} instrs) ===')
    # for every opcode used, are all instances byte-identical JP vs V90?
    for op in sorted(cnt):
        pcs=[pc for pc in ia if ia[pc]==op]
        ln=S.LENB[op]
        ndiff=0
        for pc in pcs:
            if s1a[pc:pc+ln]!=s1b[pc:pc+ln]: ndiff+=1
        note=opinfo.get(op,{}).get('note','')[:50]
        flag=' <<< OPERANDS DIFFER' if ndiff else ''
        print(f'  0x{op:02X} x{cnt[op]:<4} len={ln:<3} ndiff_instances={ndiff}{flag}  {note}')
