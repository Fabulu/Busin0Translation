import sys, struct, glob, os
sys.stdout.reconfigure(encoding='utf-8')
ee = open(r"C:/programmieren/wizardrytranslation/build/recon_tri/extract/requestbroken__ee.bin","rb").read()
res=0x011C3D00; sec2=0x011CF540
loaded = ee[res:sec2]
# compare from offset 0x18 onward (skip patched header pointers 0x14)
probe = loaded[0x20:0x220]  # 512 bytes of section1
best=[]
for fp in glob.glob("C:/programmieren/wizardrytranslation/build/packdata_resources/*.raw"):
    try: f=open(fp,"rb").read()
    except: continue
    if len(f) < 0x220: continue
    # compare section1 region
    same = sum(1 for i in range(0x200) if f[0x20+i]==probe[i])
    best.append((same, len(f), os.path.basename(fp)))
best.sort(reverse=True)
for s,ln,n in best[:8]:
    print(f"match={s}/512 size={ln} {n}")
