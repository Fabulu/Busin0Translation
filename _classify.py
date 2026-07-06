import os,glob
exe=open('extracted/SLPM_653.78','rb').read()
FOFF=0x80; VBASE=0x100000; FILESZ=0x3fdc80
seg=exe[FOFF:FOFF+FILESZ]
VEND=VBASE+FILESZ
ARENA_LO=0x4B0E00

dumps=sorted(set(glob.glob('RAMdumps/**/eeMemory.bin',recursive=True)+
                 glob.glob('build/**/eeMemory.bin',recursive=True)))

# regions below arena that differed
regs=[0x13ca00,0x2f2500,0x305900,0x307600,0x307900,0x307f00,0x308300,0x308900,
      0x308c00,0x309700,0x3a3100,0x463a00,0x463e00,0x4af400,0x4af600,0x4afa00,0x4afd00]

def loadseg(p):
    d=open(p,'rb').read(VEND)
    return d

# For each region: does the differing content VARY between dumps (game scratch=varies)
# or is it CONSTANT across all dumps that differ (=static patch)?
import hashlib
for va in regs:
    off=va-VBASE
    blk=seg[off:off+256]
    variants={}
    matchdisk=0
    for p in dumps:
        d=loadseg(p)
        if len(d)<va+256: continue
        cur=d[va:va+256]
        if cur==blk: matchdisk+=1; continue
        h=hashlib.md5(cur).hexdigest()[:8]
        variants.setdefault(h,[0,p]); variants[h][0]+=1
    print('VA %08x: matchesDisk=%d  numNonDiskVariants=%d'%(va,matchdisk,len(variants)))
    for h,(c,ex) in sorted(variants.items(),key=lambda x:-x[1][0]):
        print('     variant %s x%d  e.g.%s'%(h,c,os.path.basename(os.path.dirname(ex))))
