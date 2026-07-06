import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
f=open('extracted/SLPM_653.78','rb').read()
# search for immediate 0xFFD2 (page break) and 0x64 markers referenced near renderer
# find addiu with imm 0xffd2 -> 0x2442ffd2 style or ori/li
target=bytes.fromhex('d2ff')  # ffd2 LE
# scan code segment for halfword 0xffd2 as an immediate
seg=f[0x80:0x80+0x3fdc80]
import re
hits=[]
for i in range(0,len(seg)-4,4):
    w=struct.unpack_from('<I',seg,i)[0]
    imm=w&0xffff
    if imm==0xffd2:
        va=0x100000+i
        hits.append(va)
print('0xffd2 imm count', len(hits))
for h in hits[:40]: print(hex(h))
