import sys, struct, binascii, glob, os
sys.stdout.reconfigure(encoding='utf-8')
ee = open(r"C:/programmieren/wizardrytranslation/build/recon_tri/extract/requestbroken__ee.bin","rb").read()
sec1=0x011C3D20; sec2=0x011CF540
# Section1 base = resource offset 0x20. So resource header starts at sec1-0x20.
res = sec1-0x20
print("resource header @ RAM %08X:"%res, binascii.hexlify(ee[res:res+0x40]).decode())
size = sec2 - res
print("sec1=%08X sec2=%08X  sec2-sec1=%X  res..sec2=%X"%(sec1,sec2,sec2-sec1,sec2-res))
# Try to match this resource against build/patched_type2 R1197 and packdata
# find R1197 file
for pat in ["build/patched_type2/*1197*","build/packdata_resources/*1197*","build/**/*1197*"]:
    g=glob.glob("C:/programmieren/wizardrytranslation/"+pat, recursive=True)
    if g: print(pat, "->", g[:5])
