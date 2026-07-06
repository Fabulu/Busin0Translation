import sys, struct, binascii
sys.stdout.reconfigure(encoding='utf-8')
ee = open(r"C:/programmieren/wizardrytranslation/build/recon_tri/extract/requestbroken__ee.bin","rb").read()
def u32(a): return struct.unpack_from("<I", ee, a)[0]
sec1_base = u32(0x00564ED0)
ctx = 0x01137980
print("ctx struct @ %08X:"%ctx)
for off in range(0, 0x40, 16):
    a=ctx+off
    print("+%04X %08X "%(off,a), binascii.hexlify(ee[a:a+16]).decode())
print("around the +0x80 ref at 1137A00:")
for off in range(0x70, 0xA0, 16):
    a=ctx+off
    print("+%04X %08X "%(off,a), binascii.hexlify(ee[a:a+16]).decode())
# depth at +0x294
print("depth region +0x290:")
a=ctx+0x290
print("%08X"%a, binascii.hexlify(ee[a:a+16]).decode())
pc = u32(ctx)
print("pc field (+0)=%08X  -> rel to sec1 = %08X"%(pc, pc - sec1_base if pc>=sec1_base else pc))
