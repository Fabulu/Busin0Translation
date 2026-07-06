import struct
ee=open('_q7/chargen_ee.bin','rb').read()
# Find a single-line buffer: look for "Lives to hoard gold." followed by 0xFFFF (no FEFF)
# pattern: cells (00,c-32) for "Lives to hoard gold." then FFFF
s="Lives to hoard gold."
pat=b''.join(bytes([0x00, (ord(c)-32)&0xFF]) for c in s)
i=0
hits=[]
while True:
    i=ee.find(pat,i)
    if i<0: break
    nxt=struct.unpack_from('<H',ee,i+len(pat))[0]
    hits.append((i,hex(nxt)))
    i+=2
for h,n in hits:
    print(f"0x{h:08X} next-cell-after-line={n}")
