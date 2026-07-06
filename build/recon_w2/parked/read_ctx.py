import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee = open(r"C:/programmieren/wizardrytranslation/build/recon_tri/extract/requestbroken__ee.bin","rb").read()
def u32(a): return struct.unpack_from("<I", ee, a)[0]
# globals at VA == RAM offset for EXE region
sec1_base = u32(0x00564ED0)
sec2_base = u32(0x00564ED4)
print("sec1_base=%08X sec2_base=%08X" % (sec1_base, sec2_base))
# ctx struct: need to find pointer. The dispatcher likely stores a ctx pointer somewhere.
# print region around 0x564ED0
import binascii
print("around 0x564EC0:")
for off in range(0x564EC0, 0x564F20, 16):
    print("%08X "%off, binascii.hexlify(ee[off:off+16]).decode())
