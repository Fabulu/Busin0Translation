"""AUDIT ONLY: validate internal PACKDATA TOC in the BUILT ISO for overlaps/EOF."""
import struct, math

SECTOR = 2048
BUILT = 'build/BUSIN0_EN_v139.iso'
N = 2883

def find_packdata(path):
    with open(path,'rb') as f:
        f.seek(16*SECTOR); pvd=f.read(SECTOR)
        rl=struct.unpack_from('<I',pvd,158)[0]; rs=struct.unpack_from('<I',pvd,166)[0]
        f.seek(rl*SECTOR); root=f.read(rs)
    pos=0
    while pos<len(root):
        L=root[pos]
        if L==0: break
        nl=root[pos+32]; nm=root[pos+33:pos+33+nl].decode('ascii','replace').split(';')[0]
        if 'PACKDATA' in nm:
            return struct.unpack_from('<I',root,pos+2)[0], struct.unpack_from('<I',root,pos+10)[0]
        pos+=L
    return None,None

p_lba,p_size=find_packdata(BUILT)
p_sectors=math.ceil(p_size/SECTOR)
print(f"PACKDATA: lba={p_lba} size={p_size} sectors={p_sectors}")

with open(BUILT,'rb') as f:
    f.seek(p_lba*SECTOR)
    toc=f.read(N*12)

ents=[]
for i in range(N):
    so,sc,tc=struct.unpack_from('<III',toc,i*12)
    ents.append((i,so,sc,tc))

# Overlap/gap check across all non-zero entries (ordered by offset), excluding header outliers
res=[e for e in ents if e[1]>=125 and e[2]>0]
res.sort(key=lambda e:e[1])
overlaps=0; gaps=0; pasteof=0
prev_end=125
for i,so,sc,tc in res:
    if so < prev_end:
        overlaps+=1
        if overlaps<=10: print(f"  OVERLAP R{i}: off={so} < prev_end={prev_end} (by {prev_end-so} sectors)")
    elif so > prev_end:
        gaps+=1
        if gaps<=5: print(f"  gap before R{i}: off={so} prev_end={prev_end} (+{so-prev_end})")
    if so+sc > p_sectors:
        pasteof+=1
        if pasteof<=10: print(f"  PAST PACKDATA EOF R{i}: off+cnt={so+sc} > {p_sectors}")
    prev_end=max(prev_end, so+sc)
print(f"\noverlaps={overlaps} gaps={gaps} past_eof={pasteof}")
print(f"highest resource end sector = {prev_end} ; PACKDATA sectors = {p_sectors}")

# header outliers
for i,so,sc,tc in ents:
    if i in (2100,1370):
        print(f"  outlier R{i}: off={so} cnt={sc} type={tc} byterange=[{so*SECTOR},{(so+sc)*SECTOR})")
