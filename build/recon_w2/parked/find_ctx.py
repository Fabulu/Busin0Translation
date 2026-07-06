import sys, struct, binascii
sys.stdout.reconfigure(encoding='utf-8')
ee = open(r"C:/programmieren/wizardrytranslation/build/recon_tri/extract/requestbroken__ee.bin","rb").read()
def u32(a): return struct.unpack_from("<I", ee, a)[0]
sec1_base = u32(0x00564ED0)  # 011C3D20
sec2_base = u32(0x00564ED4)  # 011CF540
p3 = u32(0x00564ED8)         # 01137980 ?
print("sec1=%08X sec2=%08X p3=%08X"%(sec1_base,sec2_base,p3))
# ctx struct contains pc(byte ptr at +0), callstack[16] at +8, depth at +0x294
# Find candidate ctx: a struct whose +0 holds a value that, added to sec1_base, lands inside the resource,
# OR pc is an absolute pointer near sec1_base.
# Search RAM for a word equal to sec1_base (the ctx likely stores sec1_base or a pointer into it)
target = struct.pack("<I", sec1_base)
hits = []
start = 0
data = ee
idx = data.find(target)
while idx != -1 and len(hits) < 40:
    hits.append(idx)
    idx = data.find(target, idx+1)
print("refs to sec1_base:", [hex(h) for h in hits])
