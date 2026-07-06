import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee = open(r"C:/programmieren/wizardrytranslation/build/recon_tri/extract/requestbroken__ee.bin","rb").read()
def u32(a): return struct.unpack_from("<I", ee, a)[0]
sec1=0x011C3D20; sec2=0x011CF540
# A live ctx: pc in [sec1,sec2). callstack[depth] entries also in [sec1,sec2).
res=[]
for a in range(0x00100000, 0x02000000, 4):
    v=u32(a)
    if not (sec1 <= v < sec2): continue
    # check at least one callstack slot at +8.. also in range, or depth makes sense
    depth=u32(a+0x294) if a+0x298<len(ee) else 99
    if depth>16: continue
    cs_in = 0
    for i in range(min(depth,16) if depth>0 else 0):
        cv=u32(a+8+i*4)
        if sec1<=cv<sec2: cs_in+=1
    res.append((a,v,depth,cs_in))
# prefer ones where depth>0 and cs_in==depth
print("ctx with consistent callstack:")
for a,v,depth,cs in res:
    if depth>0 and cs==depth:
        print("ctx@%08X pc=%08X rel=%05X depth=%d cs_in=%d"%(a,v,v-sec1,depth,cs))
print("--- all (depth0 too) ---")
for a,v,depth,cs in res:
    print("ctx@%08X pc=%08X rel=%05X depth=%d cs_in=%d"%(a,v,v-sec1,depth,cs))
