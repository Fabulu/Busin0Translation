import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee = open(r"C:/programmieren/wizardrytranslation/build/recon_tri/extract/requestbroken__ee.bin","rb").read()
def u32(a): return struct.unpack_from("<I", ee, a)[0]
# find jal 0x2F3330  -> opcode 3, target = (0x2F3330>>2)
tgt=(0x2F3330>>2)
word = (3<<26)|tgt
import binascii
pat=struct.pack("<I", word)
i=0x100000; hits=[]
data=ee
idx=data.find(pat,0x100000)
while idx!=-1 and idx<0x600000 and len(hits)<20:
    hits.append(idx); idx=data.find(pat,idx+1)
print("callers of run-loop 0x2F3330:", [hex(h) for h in hits])
