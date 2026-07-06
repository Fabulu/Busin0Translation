import struct, sys, hashlib
sys.stdout.reconfigure(encoding='utf-8')
SECTOR=2048
def find_packdata(iso):
    with open(iso,'rb') as f:
        f.seek(16*SECTOR); pvd=f.read(SECTOR)
        rl=struct.unpack_from('<I',pvd,158)[0]; rs=struct.unpack_from('<I',pvd,166)[0]
        f.seek(rl*SECTOR); root=f.read(rs); pos=0
        while pos<len(root):
            r=root[pos]
            if r==0: break
            nl=root[pos+32]; name=root[pos+33:pos+33+nl].decode('ascii','replace')
            if 'PACKDATA' in name: return struct.unpack_from('<I',root,pos+2)[0]
            pos+=r
def toc(iso,pl,n=2883):
    with open(iso,'rb') as f:
        f.seek(pl*SECTOR); return f.read(n*12)
def res_md5(iso,pl,t,idx):
    so,sc,tc=struct.unpack_from('<III',t,idx*12)
    with open(iso,'rb') as f:
        f.seek((pl+so)*SECTOR); d=f.read(sc*SECTOR)
    return hashlib.md5(d).hexdigest(),so,sc,tc

p7=find_packdata('build/BUSIN0_EN_v87.iso'); t7=toc('build/BUSIN0_EN_v87.iso',p7)
p9=find_packdata('build/BUSIN0_EN_v89.iso'); t9=toc('build/BUSIN0_EN_v89.iso',p9)
print('comparing all 2883 resources v87 vs v89...')
diffs=[]
for idx in range(2883):
    m7,so7,sc7,tc7=res_md5('build/BUSIN0_EN_v87.iso',p7,t7,idx)
    m9,so9,sc9,tc9=res_md5('build/BUSIN0_EN_v89.iso',p9,t9,idx)
    if m7!=m9:
        diffs.append((idx,tc7,sc7,sc9,m7[:8],m9[:8]))
print(f'{len(diffs)} resources DIFFER:')
for idx,tc,sc7,sc9,a,b in diffs:
    print(f'  R{idx} type{tc} sc {sc7}->{sc9}  {a}->{b}')
