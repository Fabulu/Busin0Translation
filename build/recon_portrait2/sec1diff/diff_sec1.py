import struct, sys, os, json, hashlib
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

def operands(sec1, pc, op):
    ln=S.LENB[op]
    return sec1[pc:pc+ln]

RESS=[int(x) for x in sys.argv[1:]] or [1196,1197]
for RES in RESS:
    a=res(JP,jl,jt,RES); b=res(V90,vl,vt,RES)
    sa=struct.unpack_from('<I',a,0x18)[0]
    sb=struct.unpack_from('<I',b,0x18)[0]
    s1a=a[0x20:sa]; s1b=b[0x20:sb]
    oka,ia=S.walk(s1a)
    okb,ib=S.walk(s1b)
    print(f'\n########## R{RES} ##########')
    print(f'JP: sec2_off=0x{sa:x} sec1_len={len(s1a)} walk_ok={oka} instrs={len(ia)}')
    print(f'V90: sec2_off=0x{sb:x} sec1_len={len(s1b)} walk_ok={okb} instrs={len(ib)}')
    pcs=sorted(set(ia)|set(ib))
    # opcode set per PC
    diffs=[]
    opcode_mismatch=[]
    only_jp=[]; only_v90=[]
    for pc in pcs:
        oa=ia.get(pc); ob=ib.get(pc)
        if oa is None: only_v90.append((pc,ob)); continue
        if ob is None: only_jp.append((pc,oa)); continue
        if oa!=ob:
            opcode_mismatch.append((pc,oa,ob)); continue
        # same opcode -> compare operands
        opa=operands(s1a,pc,oa); opb=operands(s1b,pc,ob)
        if opa!=opb:
            diffs.append((pc,oa,opa,opb))
    print(f'  PCs only in JP walk: {len(only_jp)}  only in V90 walk: {len(only_v90)}')
    if only_jp[:8]: print('   JP-only pcs:',[(hex(p),hex(o)) for p,o in only_jp[:8]])
    if only_v90[:8]: print('   V90-only pcs:',[(hex(p),hex(o)) for p,o in only_v90[:8]])
    print(f'  opcode-mismatch at same PC: {len(opcode_mismatch)}')
    for pc,oa,ob in opcode_mismatch[:20]:
        print(f'    pc=0x{pc:x} JPop=0x{oa:02X} V90op=0x{ob:02X}')
    print(f'  same-opcode OPERAND diffs: {len(diffs)}')
    # group by opcode
    from collections import Counter
    c=Counter(d[1] for d in diffs)
    print('  operand-diff count by opcode:',{hex(k):v for k,v in sorted(c.items())})
    # show every NON-0x04/0x0C/0x0D/0x14 operand diff in full
    TEXT_OPS={0x04,0x0C,0x0D,0x14}
    nontext=[d for d in diffs if d[1] not in TEXT_OPS]
    print(f'  ***NON-text/name operand diffs: {len(nontext)}***')
    for pc,op,opa,opb in nontext:
        print(f'    pc=0x{pc:x} op=0x{op:02X} len={S.LENB[op]}')
        print(f'       JP : {opa.hex()}')
        print(f'       V90: {opb.hex()}')
    # also show the text-op diffs summarized (off/cnt deltas) to confirm only remap
    for pc,op,opa,opb in diffs:
        if op in TEXT_OPS:
            # decode operands
            if op==0x04:
                ja=struct.unpack_from('>I',opa,2)[0]; jc=struct.unpack_from('>I',opa,6)[0]
                va=struct.unpack_from('>I',opb,2)[0]; vc=struct.unpack_from('>I',opb,6)[0]
                tag='0x04 off/cnt'
                pass
