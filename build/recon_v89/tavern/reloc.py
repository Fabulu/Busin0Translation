import struct, sys
sys.stdout.reconfigure(encoding='utf-8')
SECTOR=2048
def files(iso):
    with open(iso,'rb') as f:
        f.seek(16*SECTOR); pvd=f.read(SECTOR)
        rl=struct.unpack_from('<I',pvd,158)[0]; rs=struct.unpack_from('<I',pvd,166)[0]
        volsz=struct.unpack_from('<I',pvd,80)[0]
        f.seek(rl*SECTOR); root=f.read(rs); pos=0; out=[]
        while pos<len(root):
            r=root[pos]
            if r==0: break
            nl=root[pos+32]; name=root[pos+33:pos+33+nl].decode('ascii','replace')
            lba=struct.unpack_from('<I',root,pos+2)[0]; size=struct.unpack_from('<I',root,pos+10)[0]
            out.append((name.split(';')[0],lba,size)); pos+=r
        return out,volsz
for iso in ['build/BUSIN0_EN_v86.iso','build/BUSIN0_EN_v87.iso','build/BUSIN0_EN_v89.iso']:
    fl,vs=files(iso)
    pk=[x for x in fl if 'PACKDATA' in x[0]][0]
    import math
    pkend=pk[1]+math.ceil(pk[2]/SECTOR)
    print(f'\n{iso}  volsize={vs}')
    print(f'  PACKDATA lba={pk[1]} size={pk[2]} end_lba={pkend}')
    for name,lba,size in sorted(fl,key=lambda x:x[1]):
        if lba>=pk[1] and 'PACKDATA' not in name:
            print(f'    {name:20s} lba={lba} size={size}')
