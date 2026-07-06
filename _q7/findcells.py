import struct
ee=open('_q7/chargen_ee.bin','rb').read()
# Glyph cells: per prompt, BIG-ENDIAN (00 XX, char-32 in high byte).
# Renderer does lh 0x40(s1) -> 16-bit. On a LE machine lh reads halfword little-endian.
# If stored bytes are [lo, hi] = [XX, 00] in memory (LE u16 = 0x00XX) then char index = lo byte.
# If stored as BIG-ENDIAN means bytes in memory are [00, XX]? Then LE u16 = 0xXX00, high byte=XX.
# Prompt says "Glyph cells are BIG-ENDIAN (00 XX, char-32 in high byte)".
# That means memory bytes = [0x00, 0xXX]?? Actually "00 XX" written big-endian display => first byte 0x00, second 0xXX.
# lh on LE reads [b0,b1] as b0 + b1<<8 = 0x00 + XX<<8 = 0xXX00. high byte = XX = char-32. CONFIRMS high byte.
# v120 bug: lh + andi 0xff reads LOW byte = 0x00 -> squash. So fix: read HIGH byte (srl 8 or lbu offset+1).
# Let's find arrays: look for runs of [00, XX] pairs where XX in 0x21..0x7e (char range) terminated by FF FF.
import re
data=ee
# scan for terminator pattern and preceding cells; look in typical heap region 0x00400000-0x02000000
best=[]
for base in range(0x00800000, 0x02000000, 4):
    # check: at base, sequence of u16 LE where each !=0xFFFF until a 0xFFFF, len>=3
    cells=[]
    p=base
    ok=True
    for i in range(40):
        v=struct.unpack_from('<H',data,p)[0]; p+=2
        if v==0xFFFF: break
        cells.append(v)
    else:
        continue
    if len(cells)<4 or len(cells)>30: continue
    # require all cells low byte ==0 and high byte in printable char range +32 region
    if all((c&0xFF)==0 and 0x20<=((c>>8))<0xa0 for c in cells):
        chars=''.join(chr((c>>8)) for c in cells)
        best.append((base,len(cells),chars))
        if len(best)>=40: break
for b,n,s in best[:40]:
    print(f"0x{b:08X} n={n} hi-byte='{s}'")
