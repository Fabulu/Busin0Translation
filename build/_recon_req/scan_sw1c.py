import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,r"C:\programmieren\wizardrytranslation\build\_recon_req")
from disas import dec, exe, VA_BASE
# scan whole .text for sw rt, 0x1c(rs)
# op==0x2B (sw), imm==0x1c
TEXT_START=0x100000
TEXT_END=0x100000+len(exe)-0x80
va=TEXT_START
hits=[]
while va < TEXT_END-4:
    off=va-VA_BASE
    if off<0 or off+4>len(exe):
        va+=4; continue
    w=struct.unpack('<I',exe[off:off+4])[0]
    op=(w>>26)&0x3F; rs=(w>>21)&0x1F; rt=(w>>16)&0x1F; imm=w&0xFFFF
    if op==0x2B and imm==0x1c:
        hits.append((va,w,rs,rt))
    va+=4
REG=["zero","at","v0","v1","a0","a1","a2","a3","t0","t1","t2","t3","t4","t5","t6","t7","s0","s1","s2","s3","s4","s5","s6","s7","t8","t9","k0","k1","gp","sp","s8","ra"]
print(f"total sw ?,0x1c(?): {len(hits)}")
for va,w,rs,rt in hits:
    print(f"{va:08X}  sw ${REG[rt]}, 0x1c(${REG[rs]})")
