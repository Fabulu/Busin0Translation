import struct, json, sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir('C:/programmieren/wizardrytranslation')
SECTOR = 2048
ISO = 'build/BUSIN0_EN_v92.iso'

iso = open(ISO,'rb')
iso.seek(16*SECTOR); pvd = iso.read(SECTOR)
root_lba = struct.unpack_from('<I', pvd, 158)[0]
root_size = struct.unpack_from('<I', pvd, 166)[0]
iso.seek(root_lba*SECTOR); root_dir = iso.read(root_size)
pos=0; pack_lba=None; pack_size=None
while pos < len(root_dir):
    rl = root_dir[pos]
    if rl==0: break
    nl = root_dir[pos+32]
    name = root_dir[pos+33:pos+33+nl].decode('ascii','replace')
    if 'PACKDATA' in name:
        pack_lba = struct.unpack_from('<I', root_dir, pos+2)[0]
        pack_size = struct.unpack_from('<I', root_dir, pos+10)[0]
        print(f'PACKDATA: lba={pack_lba} size={pack_size} ({pack_size//SECTOR} sectors)')
        break
    pos+=rl

# Read manifest to know how many TOC entries
manifest = json.load(open('extracted/packdata_resources/manifest.json', encoding='utf-8'))
n = len(manifest)
print(f'manifest entries: {n}')

# Read TOC from PACKDATA inside ISO
iso.seek(pack_lba*SECTOR)
toc_raw = iso.read(12*n)
toc = [struct.unpack_from('<III', toc_raw, i*12) for i in range(n)]

# R2654 is index 2654
idx = 2654
so, sc, tc = toc[idx]
print(f'R2654 TOC: sector_off={so} sector_cnt={sc} type_code={tc}')
# read it from ISO
iso.seek(pack_lba*SECTOR + so*SECTOR)
data = iso.read(sc*SECTOR)
open('build/recon_fvs/vera/r2654_from_v92iso.raw','wb').write(data)
print(f'wrote {len(data)} bytes')

# --- also extract R1892 from ISO ---
idx2=1892
so2,sc2,tc2=toc[idx2]
print(f'\nR1892 TOC: sector_off={so2} sector_cnt={sc2} type_code={tc2}')
iso.seek(pack_lba*SECTOR + so2*SECTOR)
data2=iso.read(sc2*SECTOR)
open('build/recon_fvs/vera/r1892_from_v92iso.raw','wb').write(data2)
prist1892=open('extracted/packdata_raw/1892_type20.raw','rb').read()
print(f'R1892 from ISO: {len(data2)} bytes; pristine {len(prist1892)} bytes')
print('R1892 ISO == pristine:', data2[:len(prist1892)]==prist1892 or data2.rstrip(b"\x00")==prist1892.rstrip(b"\x00"))
print('R1892 ISO byte-identical to pristine (trimmed):', data2.rstrip(b'\x00')==prist1892.rstrip(b'\x00'))
