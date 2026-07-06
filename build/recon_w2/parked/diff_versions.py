import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee = open(r"C:/programmieren/wizardrytranslation/build/recon_tri/extract/requestbroken__ee.bin","rb").read()
res=0x011C3D00
# RAM-loaded R1197 (v96). But RAM only spans 47168; section1 we can read.
ram = ee[res:res+0x14000]  # generous
patched = open("C:/programmieren/wizardrytranslation/build/patched_type2/1197_type02.raw","rb").read()
pack    = open("C:/programmieren/wizardrytranslation/build/packdata_resources/1197_type02.raw","rb").read()
backup  = open("C:/programmieren/wizardrytranslation/build/packdata_resources_backup/1197_type02.raw","rb").read()
# header at +4 = section1 size? we saw 1fb8 at +4 in RAM. Let's read it from patched.
def hdr(b,n):
    print(n, "first 0x40:", b[:0x40].hex())
hdr(ram,"RAM(v96)")
hdr(patched,"patched(v99)")
hdr(pack,"pack(v99)")
hdr(backup,"backup(pre)")
# section1 size field
import struct
print("section1 size patched @4:", struct.unpack_from("<I",patched,4)[0], "ram@4:", struct.unpack_from("<I",ram,4)[0])
