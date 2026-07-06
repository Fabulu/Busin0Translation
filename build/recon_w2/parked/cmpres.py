import sys, struct, binascii
sys.stdout.reconfigure(encoding='utf-8')
ee = open(r"C:/programmieren/wizardrytranslation/build/recon_tri/extract/requestbroken__ee.bin","rb").read()
res=0x011C3D00; sec2=0x011CF540
loaded = ee[res:sec2]
print("loaded resource size (RAM span):", len(loaded))
for name in ["patched_type2","packdata_resources","packdata_resources_backup"]:
    try:
        f=open(f"C:/programmieren/wizardrytranslation/build/{name}/1197_type02.raw","rb").read()
    except Exception as e:
        print(name, "ERR", e); continue
    # match: does loaded start equal file?
    eqlen=0
    m=min(len(f),len(loaded))
    for i in range(m):
        if f[i]==loaded[i]: eqlen+=1
        else: break
    print(f"{name}: filesize={len(f)} first-diff at {eqlen:#x} ({'MATCH' if eqlen>=m else 'differ'})")
