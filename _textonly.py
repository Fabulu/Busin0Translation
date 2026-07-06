import glob
exe=open('extracted/SLPM_653.78','rb').read()
FOFF=0x80; VBASE=0x100000; FILESZ=0x3fdc80
seg=exe[FOFF:FOFF+FILESZ]
# Our known patch sites (VA spans) to exclude
patch_sites=[(0x2f2560,0x2f2570),(0x305980,0x3059a0),(0x3076f8,0x308d80),
             (0x3097a0,0x309760),(0x30973c,0x309760),(0x3a31a0,0x3a31b0),
             (0x463af0,0x463f50)]
def in_patch(va): return any(lo<=va<hi for lo,hi in patch_sites)
# .text is roughly VA 0x100000..0x47e000 (code+rodata); libgraph .data starts ~0x4af400
# Scan 0x100000..0x47e000 EXCLUDING patch sites: any non-patch diff = game self-mod
dumps=sorted(set(glob.glob('RAMdumps/**/eeMemory.bin',recursive=True)+
                 glob.glob('build/**/eeMemory.bin',recursive=True)))
unexplained=set()
TEXT_HI=0x47e000
for p in dumps:
    f=open(p,'rb'); f.seek(VBASE); d=f.read(TEXT_HI-VBASE); f.close()
    if len(d)<TEXT_HI-VBASE: continue
    for i in range(len(d)):
        if d[i]!=seg[i]:
            va=VBASE+i
            if not in_patch(va): unexplained.add(va)
print('UNEXPLAINED diffs in .text/.rodata 0x100000..0x47e000 (excl. our patch sites):')
if not unexplained: print('  NONE — code segment is byte-identical to disk except our patches')
else:
    s=sorted(unexplained); runs=[]
    for v in s:
        if runs and v-runs[-1][1]<=8: runs[-1][1]=v+1
        else: runs.append([v,v+1])
    for lo,hi in runs: print('  %08x-%08x'%(lo,hi))
