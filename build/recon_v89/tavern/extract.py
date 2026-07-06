import struct, sys, hashlib, os
sys.stdout.reconfigure(encoding='utf-8')
SECTOR=2048

def find_packdata(iso):
    with open(iso,'rb') as f:
        f.seek(16*SECTOR); pvd=f.read(SECTOR)
        root_lba=struct.unpack_from('<I',pvd,158)[0]
        root_size=struct.unpack_from('<I',pvd,166)[0]
        f.seek(root_lba*SECTOR); root=f.read(root_size)
        pos=0
        while pos<len(root):
            rl=root[pos]
            if rl==0: break
            nl=root[pos+32]
            name=root[pos+33:pos+33+nl].decode('ascii','replace')
            if 'PACKDATA' in name:
                lba=struct.unpack_from('<I',root,pos+2)[0]
                size=struct.unpack_from('<I',root,pos+10)[0]
                return lba,size
            pos+=rl
    return None

def extract_res(iso, pack_lba, idx, n_entries=2883):
    with open(iso,'rb') as f:
        f.seek(pack_lba*SECTOR)
        toc=f.read(n_entries*12)
        so,sc,tc=struct.unpack_from('<III',toc,idx*12)
        # offset is in sectors relative to PACKDATA start
        f.seek((pack_lba+so)*SECTOR)
        data=f.read(sc*SECTOR)
    return so,sc,tc,data

for iso in ['build/BUSIN0_EN_v87.iso','build/BUSIN0_EN_v89.iso']:
    pl,ps=find_packdata(iso)
    print(f'\n=== {iso} ===')
    print(f'PACKDATA lba={pl} size={ps} ({ps//SECTOR} sectors, {(ps+SECTOR-1)//SECTOR} ceil)')
    for idx in [2147,2155,2124,1365]:
        so,sc,tc,data=extract_res(iso,pl,idx)
        h=hashlib.md5(data).hexdigest()
        print(f'  R{idx}: TOC so={so} sc={sc} tc={tc} | len={len(data)} md5={h}')
        tag=os.path.basename(iso).split('_')[-1].replace('.iso','')
        open(f'build/recon_v89/tavern/R{idx}_{tag}.raw','wb').write(data)
