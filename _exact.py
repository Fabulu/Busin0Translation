import os,glob,hashlib
exe=open('extracted/SLPM_653.78','rb').read()
FOFF=0x80; VBASE=0x100000; FILESZ=0x3fdc80
seg=exe[FOFF:FOFF+FILESZ]
VEND=VBASE+FILESZ
CAVE=0x4AB554
ARENA_LO=0x4B0E00
dumps=sorted(set(glob.glob('RAMdumps/**/eeMemory.bin',recursive=True)+
                 glob.glob('build/**/eeMemory.bin',recursive=True)))

# For every dump, find EXACT differing byte spans below arena (VBASE..ARENA_LO)
# merge into global span set, record min distance to cave
spans={}   # (lo,hi) approx -> count
hi_va_below=ARENA_LO
allbytes=set()
for p in dumps:
    f=open(p,'rb'); 
    f.seek(VBASE); d=f.read(hi_va_below-VBASE); f.close()
    if len(d)<hi_va_below-VBASE: continue
    i=0; N=len(d)
    while i<N:
        if d[i]!=seg[i]:
            j=i
            while j<N and d[j]!=seg[j]: j+=1
            allbytes.add((VBASE+i, VBASE+j))
            i=j
        else: i+=1

# merge overlapping/adjacent (<64 gap) spans
sp=sorted(allbytes)
merged=[]
for lo,hi in sp:
    if merged and lo-merged[-1][1]<=64: merged[-1]=(merged[-1][0],max(merged[-1][1],hi))
    else: merged.append((lo,hi))
print('Distinct differing byte-spans below arena (merged<=64B gaps):')
for lo,hi in merged:
    dist=min(abs(lo-CAVE),abs(hi-CAVE))
    near=' <-- within 4KB of cave' if dist<0x1000 else ''
    print('  %08x-%08x  (len %4d)  dist_to_cave=%#x%s'%(lo,hi,hi-lo,dist,near))
print()
print('CAVE=%08x  ARENA_LO=%08x'%(CAVE,ARENA_LO))
# explicit: any differing byte in [CAVE-0x800, ARENA_LO) ?
print('Any diff in [0x4ab000,0x4b0e00)?')
hit=[m for m in merged if m[1]>0x4ab000 and m[0]<ARENA_LO]
print('  spans:',hit if hit else 'NONE')
