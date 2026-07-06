import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
# Decode the glyph array (s5+0x40 narration / s3+0x40 chargen) from eeMemory by
# locating the descriptor. We don't know the live ptr, so scan eeMemory for the
# known glyph sequence of "A heavy fog had..." to validate gid==char-32.
ee=open(sys.argv[1],'rb').read()
# narration glyph array: u16 LE? The renderer reads lh (signed 16) at +0x40 stride 2.
# In RAM these are stored as native (LE) 16-bit. gid for 'A'=33,' '=0,'h'=72...
def enc(c): return ord(c)-32
target="A heavy fog had"
seq=[enc(c) for c in target]
# search for the LE u16 sequence
pat=b''.join(struct.pack('<H',g) for g in seq)
idx=ee.find(pat)
print(f"LE u16 seq for {target!r}: found at {idx:#x}" if idx>=0 else "LE u16 not found")
# also try as the descriptor being at struct+0x40, so the array start - 0x40
if idx>=0:
    print(f"  -> descriptor base would be {idx-0x40:#x}")
    # dump following words till 0xFFFF
    o=idx; out=[]
    for k in range(80):
        w=struct.unpack_from('<H',ee,o+k*2)[0]
        if w==0xFFFF: break
        out.append(w)
    print("  glyphs:", out)
    print("  text:", ''.join(chr(g+32) if 0<=g<95 else '?' for g in out))
