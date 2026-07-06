import sys
sys.stdout.reconfigure(encoding='utf-8')
ee=open("C:/programmieren/wizardrytranslation/build/recon_tri/extract/veraisjapanese__ee.bin","rb").read()
# BABA name-value run = 34,33,34,33 as LE u16 -> bytes 22 00 21 00 22 00 21 00
import struct
def pat(vals): return b''.join(struct.pack('<H',v) for v in vals)
baba=pat([34,33,34,33])
# よしほく hiragana name-values: need to figure. Search BABA occurrences first.
print("BABA u16-LE occurrences:")
i=0; cnt=0
while True:
    j=ee.find(baba,i)
    if j<0: break
    print(f"  @0x{j:X}")
    i=j+1; cnt+=1
    if cnt>40: break
print("total",cnt)
