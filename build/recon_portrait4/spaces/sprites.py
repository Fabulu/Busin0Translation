import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open('build/recon_portrait4/extract/Toolongspaces__ee.bin','rb').read()
# The render ctx s5 has a sprite array at 0x8(ctx); each sprite stride 0xC, field +6 = u16 (0x80 flag), and likely XY at +0/+2/+4.
# Find the FontDispSet record: gp=0x504FF0; record ptr at gp-0x6234 = 0x4FEDBC (RAM va). file off = va (since p2s vaddr0=fileoff0)
def rd32(a): return struct.unpack_from('<I',ee,a)[0]
def rd16(a): return struct.unpack_from('<H',ee,a)[0]
gp=0x504FF0
recptr_addr=gp-0x6234
recptr=rd32(recptr_addr)
print("gp-0x6234 @0x%X -> record ptr=0x%X"%(recptr_addr,recptr))
if 0<recptr<0x2000000:
    print("record dump (0x40 bytes):")
    for o in range(0,0x40,4):
        print("  +0x%02X = 0x%08X"%(o,rd32(recptr+o)))
    sprbuf=rd32(recptr+0x8)
    cnt=rd32(recptr+0x1C)
    print("sprite buf=0x%X glyph count(0x1C)=%d"%(sprbuf,cnt))
