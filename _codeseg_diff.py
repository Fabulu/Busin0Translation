import os,glob
exe=open('extracted/SLPM_653.78','rb').read()
FOFF=0x80; VBASE=0x100000; FILESZ=0x3fdc80
seg=exe[FOFF:FOFF+FILESZ]      # seg[i] -> VA VBASE+i
VEND=VBASE+FILESZ              # 0x4fdc80
CAVE=0x4AB554
ARENA_LO=0x4B0E00

dumps=sorted(set(glob.glob('RAMdumps/**/eeMemory.bin',recursive=True)+
                 glob.glob('build/**/eeMemory.bin',recursive=True)))

# We compare VA VBASE..VEND. For each dump, collect differing runs (granularity 256B)
# Aggregate: for each 256B block index over the segment, count how many dumps differ.
BLK=256
nblk=(FILESZ+BLK-1)//BLK
diffcount=[0]*nblk
ndumps=0
percave=[]
for p in dumps:
    sz=os.path.getsize(p)
    if sz < VEND: 
        continue
    d=open(p,'rb').read(VEND)   # read up to VEND only
    if len(d)<VEND: continue
    ndumps+=1
    dseg=d[VBASE:VBASE+FILESZ]  # ee[VA]==VA index directly
    # block compare
    for b in range(nblk):
        a=b*BLK; e=min(a+BLK,FILESZ)
        if dseg[a:e]!=seg[a:e]:
            diffcount[b]+=1
    # specifically check cave 0x4AB554 byte region & immediate context
    co=CAVE-VBASE
    percave.append((p, dseg[co-16:co+128]!=seg[co-16:co+128]))

print('compared dumps:',ndumps)
# Report blocks that differ in ANY dump, BELOW arena, grouped into contiguous VA ranges
arena_off=ARENA_LO-VBASE
ranges=[]
cur=None
for b in range(nblk):
    va=VBASE+b*BLK
    if diffcount[b]>0:
        if cur is None: cur=[va, va+BLK, diffcount[b], diffcount[b]]
        else:
            cur[1]=va+BLK; cur[2]=max(cur[2],diffcount[b]); cur[3]=min(cur[3],diffcount[b])
    else:
        if cur is not None: ranges.append(cur); cur=None
if cur: ranges.append(cur)
print('=== Differing VA ranges (block 256B) across all dumps ===')
for lo,hi,mx,mn in ranges:
    tag=''
    if lo< ARENA_LO and hi> ARENA_LO: tag=' (SPANS arena boundary)'
    elif hi<=ARENA_LO: tag=' [BELOW arena = code/data seg]'
    else: tag=' [arena/BSS region]'
    print('  %08x-%08x  diffdumps max=%d min=%d%s'%(lo,hi,mx,mn,tag))
print()
print('=== Cave context 0x4AB554-0x4AB5D4 differs from DISK in: ===')
for p,diff in percave:
    if diff: print('  CHANGED', p)
nch=sum(1 for _,d in percave if d)
print('cave changed in %d/%d dumps'%(nch,len(percave)))
