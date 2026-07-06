import struct, sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools')
from sec1_disasm import walk
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
            if 'PACKDATA' in name:
                return struct.unpack_from('<I',root,pos+2)[0], struct.unpack_from('<I',root,pos+10)[0]
            pos+=L
    raise RuntimeError('no packdata')
def read_toc(iso):
    lba,size=find_packdata(iso)
    with open(iso,'rb') as f:
        f.seek(lba*SECTOR); toc=[struct.unpack('<III',f.read(12)) for _ in range(N)]
    return lba,toc
def res(iso,lba,toc,i):
    so,sc,tc=toc[i]
    with open(iso,'rb') as f:
        f.seek((lba+so)*SECTOR); return f.read(sc*SECTOR),tc

HEADER=0x20
def sec1_of(data):
    sec2_off=struct.unpack_from('<I',data,0x18)[0]
    return data[HEADER:sec2_off]

def gate_ops(sec1):
    ok,instrs=walk(sec1)
    out={}
    for pc,opc in sorted(instrs.items()):
        if opc in (0x17,0x18,0x0C,0x0D):
            ln={0x17:50,0x18:50,0x0C:6,0x0D:6}[opc]
            out[pc]=(opc, bytes(sec1[pc:pc+ln]))
    return ok,out

JP='Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso'
for V,tag in [('build/BUSIN0_EN_v90.iso','v90'),('build/BUSIN0_EN_v84.iso','v84')]:
    if not os.path.exists(V):
        print(tag,'ISO missing'); continue
    jl,jt=read_toc(JP); vl,vt=read_toc(V)
    print(f'\n========== JP vs {tag} ==========')
    for ridx in (1196,1197,1198,1200,1203,1354):
        jdat,jtc=res(JP,jl,jt,ridx); vdat,vtc=res(V,vl,vt,ridx)
        try:
            js=sec1_of(jdat); vs=sec1_of(vdat)
        except Exception as e:
            print(f' R{ridx}: sec1 parse err {e}'); continue
        jok,jg=gate_ops(js); vok,vg=gate_ops(vs)
        # compare gate opcodes by pc-set + bytes
        diffs=[]
        common=set(jg)&set(vg)
        for pc in sorted(common):
            if jg[pc]!=vg[pc]:
                diffs.append((pc,jg[pc],vg[pc]))
        onlyj=set(jg)-set(vg); onlyv=set(vg)-set(jg)
        print(f' R{ridx}: JP walk ok={jok} {tag} ok={vok} | gate-ops JP={len(jg)} {tag}={len(vg)} | '
              f'byte-diffs={len(diffs)} only-in-JP={len(onlyj)} only-in-{tag}={len(onlyv)}')
        for pc,a,b in diffs[:6]:
            print(f'    pc=0x{pc:X} op=0x{a[0]:02X} JP={a[1].hex()} {tag}={b[1].hex()}')
