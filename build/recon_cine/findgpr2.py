import struct,sys
sys.stdout.reconfigure(encoding='utf-8')
d=open("RAMdumps/Nameentrystate_extracted/PCSX2 Internal Structures.dat","rb").read()
# relax: r0 zero (16 bytes), and at least gp in 0x100000..0x600000
best=[]
for off in range(0, len(d)-512, 4):
    if d[off:off+16]!=b'\x00'*16: continue
    gp=struct.unpack_from("<I",d,off+28*16)[0]
    if 0x100000<=gp<=0x600000:
        # check ra and sp loosely
        sp=struct.unpack_from("<I",d,off+29*16)[0]
        ra=struct.unpack_from("<I",d,off+31*16)[0]
        best.append((off,gp,sp,ra))
print(len(best),"candidates")
from collections import Counter
c=Counter(g for _,g,_,_ in best)
for gp,n in c.most_common(15):
    print(f"gp=0x{gp:08X} count={n}")
