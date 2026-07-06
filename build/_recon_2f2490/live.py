import sys,struct,zipfile,io
sys.stdout.reconfigure(encoding='utf-8')
p2s=sys.argv[1]
z=zipfile.ZipFile(p2s)
ee=None
for n in z.namelist():
    if 'eeMemory' in n: ee=z.read(n)
print("EE size",len(ee))
def u8(a): return ee[a]
def u16(a): return struct.unpack('<H',ee[a:a+2])[0]
def s16(a): return struct.unpack('<h',ee[a:a+2])[0]
def u32(a): return struct.unpack('<I',ee[a:a+4])[0]
def be16(a): return struct.unpack('>H',ee[a:a+2])[0]

# verify patch
print("0x308328 =",hex(u32(0x308328)),"(li a0,8 = 0x24040008)")
print("0x4FED18 screen-mode =",u32(0x4FED18))

desc=0x1137AC0
print("\n=== descriptor",hex(desc),"===")
print("desc[0x00] ptr =",hex(u32(desc+0x00)))
print("desc[0x04] ptr =",hex(u32(desc+0x04)))
print("desc[0x1c] box_width =",s16(desc+0x1c),"(u16",u16(desc+0x1c),")")
print("desc[0x3c] boxX =",s16(desc+0x3c),"(u16",u16(desc+0x3c),")")
print("desc[0x3e] boxY =",s16(desc+0x3e),"(u16",u16(desc+0x3e),")")
print("desc[0x2c] (depth) =",hex(u32(desc+0x2c)))
print("desc[0x2a7] align =",u8(desc+0x2a7))

# per-line glyph count array at s0+0x40 where s0=desc? The recon said s0+0x40.
# s0 is the descriptor base in this func. Print 0x40..0x60
print("\n=== s0+0x40 per-line glyph count array (lh) ===")
for i in range(8):
    print(f"  [{i}] +{0x40+i*2:#x} = {s16(desc+0x40+i*2)}")

# Patch-14 ADV LUT at 0x4C7564, LEFTSHIFT LUT at 0x4C7690
print("\n=== ADV LUT 0x4C7564 (gid 0..40) ===")
print([u8(0x4C7564+i) for i in range(42)])
print("=== LEFTSHIFT LUT 0x4C7690 (gid 0..40) ===")
print([u8(0x4C7690+i) for i in range(42)])
