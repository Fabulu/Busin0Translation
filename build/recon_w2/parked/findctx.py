import sys, struct, binascii
sys.stdout.reconfigure(encoding='utf-8')
ee = open(r"C:/programmieren/wizardrytranslation/build/recon_tri/extract/requestbroken__ee.bin","rb").read()
def u32(a): return struct.unpack_from("<I", ee, a)[0]
def u16(a): return struct.unpack_from("<H", ee, a)[0]
sec1=0x011C3D20; sec2=0x011CF540
# scan all 4-byte aligned words for a value in [sec1, sec2) — candidate pc fields
# then check struct shape: +0x294 depth small, +0x29C counter
cands=[]
for a in range(0x00100000, 0x02000000, 4):
    v=struct.unpack_from("<I", ee, a)[0]
    if sec1 <= v < sec2:
        # candidate ctx at 'a' (pc field). check depth +0x294 is small
        if a+0x2A0 < len(ee):
            depth=u32(a+0x294)
            flags=u32(a+0x290)
            cnt=u16(a+0x29C)
            if depth<=16:
                cands.append((a,v,depth,flags,cnt))
print("count cands:", len(cands))
for c in cands[:30]:
    a,v,depth,flags,cnt=c
    print("ctx@%08X pc=%08X (rel %05X) depth=%d flags=%08X cnt=%d"%(a,v,v-sec1,depth,flags,cnt))
