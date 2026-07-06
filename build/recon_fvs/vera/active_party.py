import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open('build/recon_portrait4/extract/request__ee.bin','rb').read()
# The party bar shows leader 'A A' THEN Vera. So active party slot1=player(A A), slot2=Vera.
# 0x560xxx and 0xDC1xxx are the FULL roster (all NPCs in order), not the active party.
# The active party is a separate small struct/pointer set. Vera's roster struct base ~0x5601E2 (idx field 0x13).
# Find pointers to 0x5601xx or 0xDC1Axx (active party referencing roster)
import struct as S
def find_ptr(target,lo=0x100000,hi=0x2000000):
    pat=S.pack('<I',target)
    res=[];i=ee.find(pat,lo)
    while i!=-1 and i<hi and len(res)<20:
        res.append(i);i=ee.find(pat,i+1)
    return res
for t in (0x5601F2,0x5601E2,0x5601E0,0xDC1AF2):
    print('ptr->0x%X:'%t,['0x%X'%x for x in find_ptr(t)])
