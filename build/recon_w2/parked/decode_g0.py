import sys, struct, json, glob
sys.stdout.reconfigure(encoding='utf-8')
# Build reverse glyph map: enc(char)->value. Find the encoder map.
# build_v9 uses enc(). Let's find the glyph map.
b=open("C:/programmieren/wizardrytranslation/build/patched_type2/1197_type02.raw","rb").read()
so=struct.unpack_from("<I",b,0x18)[0]; ss=struct.unpack_from("<I",b,0x14)[0]
sec2=b[so:so+ss]
words=[struct.unpack_from(">H",sec2,i*2)[0] for i in range(47)]
# guess: 0x30='0'? Common ASCII glyph mapping: value = ascii? 0x34='4' ascii. But text "THE FOOL"? 
# 0034 0048 0045 -> if these are A=0x.. Let's try value-? Map by: 'A'? 
# Standard in this project: glyphs at char-32 region OR direct. Try ascii: chr(w) 
print("raw words:", " ".join("%04X"%w for w in words))
# try interpret 0x00 as space sep, FFFE as newline, and map letters: maybe 0x34..= 'T'? 
# 0x34=52. 'T'=84. diff 32. So glyph = ascii-32!  0x34+32=0x54='T'. 0x48+32=0x68='h'? no 'H'=0x48+? 
def g2c(w):
    if w==0x0000: return ' '
    if w==0xFFFE: return '\n'
    if w==0xFFFF: return '<END>'
    if w<0x80: 
        c=w+32
        return chr(c) if 32<=c<127 else "[%02X]"%w
    return "[%04X]"%w
print("decoded:", "".join(g2c(w) for w in words))
