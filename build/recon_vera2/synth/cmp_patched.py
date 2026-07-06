import sys, struct, os
sys.stdout.reconfigure(encoding='utf-8')
BASE="C:/programmieren/wizardrytranslation"
pris=open(BASE+"/extracted/packdata_raw/1892_type20.raw",'rb').read()
buildp=BASE+"/build/packdata_resources/1892_type20.raw"
print("pristine R1892 rec0 @0x142:",pris[0x142:0x14C].hex())
print("pristine R1892 rec9(Vera) @0xBF2:",pris[0xBF2:0xBFE].hex())
if os.path.exists(buildp):
    b=open(buildp,'rb').read()
    print("BUILD R1892 rec0 @0x142:",b[0x142:0x14C].hex())
    print("BUILD R1892 rec9(Vera) @0xBF2:",b[0xBF2:0xC00].hex())
else:
    print("NO build/packdata_resources/1892_type20.raw")
# decode rec0 pristine as u16
print("pristine rec0 u16:",[struct.unpack_from('<H',pris,0x142+i*2)[0] for i in range(5)])
print("pristine Vera u16:",[struct.unpack_from('<H',pris,0xBF2+i*2)[0] for i in range(6)])
