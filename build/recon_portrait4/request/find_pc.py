import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
EE='build/recon_portrait4/extract/request__ee.bin'
ee=open(EE,'rb').read()
def rd32(a): return struct.unpack_from('<I',ee,a)[0]
import struct as S
def sec1(path):
    d=open(path,'rb').read(); s2=S.unpack_from('<I',d,0x18)[0]; return d[0x20:s2], s2, d
c1197,c1197_s2,c1197_full=sec1('build/packdata_resources/1197_type02.raw')
RESBASE=0x011C3D20  # where sec1 starts in EE (note: this is sec1[0]; full resource header is 0x20 before)
FULLBASE=RESBASE-0x20
sec1len=len(c1197)
sec2base=FULLBASE+c1197_s2
print(f"R1197 resident: full@0x{FULLBASE:X} sec1@0x{RESBASE:X} (len {sec1len}) sec2@0x{sec2base:X}")
# Find pointers anywhere in EE that point INTO sec1 [RESBASE, RESBASE+sec1len)
lo,hi=RESBASE,RESBASE+sec1len
hits=[]
for a in range(0x300000,0x600000,4):  # scan BSS/globals region
    v=rd32(a)
    if lo<=v<hi:
        hits.append((a,v))
print(f"pointers into R1197 sec1 from globals 0x300000-0x600000: {len(hits)}")
for a,v in hits[:40]:
    off=v-RESBASE
    print(f"  global 0x{a:X} -> sec1+0x{off:X} (0x{v:X})")
