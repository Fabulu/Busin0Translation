import glob
exe=open('extracted/SLPM_653.78','rb').read()
FOFF=0x80; VBASE=0x100000; FILESZ=0x3fdc80
seg=exe[FOFF:FOFF+FILESZ]
CAVE=0x4AB554
LO=0x4A8000; HI=0x4B0E00   # window below arena around cave
dumps=sorted(set(glob.glob('RAMdumps/**/eeMemory.bin',recursive=True)+
                 glob.glob('build/**/eeMemory.bin',recursive=True)))
diffbytes=set()
for p in dumps:
    f=open(p,'rb'); f.seek(LO); d=f.read(HI-LO); f.close()
    if len(d)<HI-LO: continue
    base=LO-VBASE
    for i in range(len(d)):
        if d[i]!=seg[base+i]: diffbytes.add(LO+i)
print('Window %08x..%08x around CAVE %08x'%(LO,HI,CAVE))
if not diffbytes:
    print('  NO differing bytes anywhere in window across all dumps')
else:
    s=sorted(diffbytes); runs=[]
    for v in s:
        if runs and v-runs[-1][1]<=8: runs[-1][1]=v+1
        else: runs.append([v,v+1])
    for lo,hi in runs:
        rel=lo-CAVE
        print('  %08x-%08x  (cave%+#x)'%(lo,hi,rel))
# cave content in disk: what is there pristine? (the relocated cave target)
print()
print('Pristine bytes AT cave 0x4ab554..0x4ab5d4:')
o=CAVE-VBASE
import struct
allzero=all(b==0 for b in seg[o:o+0x80])
print('  all-zero padding?', allzero)
print('  hex:', seg[o:o+48].hex())
# show what precedes (jr ra epilogue claim)
print('  preceding 16 bytes (0x4ab544):', seg[CAVE-VBASE-16:CAVE-VBASE].hex())
