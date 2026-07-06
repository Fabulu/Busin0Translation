import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
BASE='C:/programmieren/wizardrytranslation'
SECTOR=2048
iso=open(f'{BASE}/build/BUSIN0_EN_v91.iso','rb')
# find PACKDATA.DIG in root dir via PVD
iso.seek(16*SECTOR); pvd=iso.read(SECTOR)
root_lba=struct.unpack_from('<I',pvd,158)[0]; root_size=struct.unpack_from('<I',pvd,166)[0]
iso.seek(root_lba*SECTOR); root=iso.read(root_size)
pos=0; pack_lba=pack_size=None
while pos<len(root):
    rl=root[pos]
    if rl==0: break
    nl=root[pos+32]; name=root[pos+33:pos+33+nl].decode('ascii','replace')
    if 'PACKDATA' in name:
        pack_lba=struct.unpack_from('<I',root,pos+2)[0]
        pack_size=struct.unpack_from('<I',root,pos+10)[0]
    pos+=rl
print('PACKDATA lba',pack_lba,'size',pack_size)
iso.seek(pack_lba*SECTOR)
pack=iso.read(pack_size)
open(f'{BASE}/build/recon_portrait4/r2654/PACKDATA_v91.bin','wb').write(pack)
print('saved PACKDATA, first 32 bytes:', pack[:32].hex())
