import struct, sys, hashlib
sys.stdout.reconfigure(encoding='utf-8')
SECTOR=2048
def get_exe(iso):
    with open(iso,'rb') as f:
        f.seek(16*SECTOR); pvd=f.read(SECTOR)
        rl=struct.unpack_from('<I',pvd,158)[0]; rs=struct.unpack_from('<I',pvd,166)[0]
        f.seek(rl*SECTOR); root=f.read(rs); pos=0
        while pos<len(root):
            r=root[pos]
            if r==0: break
            nl=root[pos+32]; name=root[pos+33:pos+33+nl].decode('ascii','replace')
            if 'SLPM' in name:
                lba=struct.unpack_from('<I',root,pos+2)[0]; size=struct.unpack_from('<I',root,pos+10)[0]
                f.seek(lba*SECTOR); return f.read(size)
            pos+=r
e7=get_exe('build/BUSIN0_EN_v87.iso'); e9=get_exe('build/BUSIN0_EN_v89.iso')
print('EXE v87', len(e7), hashlib.md5(e7).hexdigest())
print('EXE v89', len(e9), hashlib.md5(e9).hexdigest())
print('identical:', e7==e9)
