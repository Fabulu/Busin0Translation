import sys, struct
sys.stdout.reconfigure(encoding='utf-8')

CUR='C:/programmieren/wizardrytranslation/build/recon_portrait3/extract/MissingPortraitAndFuckedDialogue__ee.bin'
REF='C:/programmieren/wizardrytranslation/build/recon_portrait2/extract/Firstdialogue__ee.bin'
RAW='C:/programmieren/wizardrytranslation/extracted/packdata_raw'
R1251=open(f'{RAW}/1251_type01.raw','rb').read()
def load(p): return open(p,'rb').read()
cur=load(CUR); ref=load(REF)

CGSLOT=0x509F80
for tag,buf in (('CUR',cur),('REF',ref)):
    ptr=struct.unpack_from('<I',buf,CGSLOT)[0]
    print(f"{tag}: cgslot ptr=0x{ptr:08X}")
    if 0 < ptr < len(buf):
        blob=buf[ptr:ptr+64]
        print(f"   data@ptr: {blob[:32].hex()}")
        # does R1251 payload appear at/near ptr? compare to R1251[0:64] and R1251[0xA1:..]
        # find R1251 header signature in buf near ptr
        sig=R1251[:32]
        idx=buf.find(sig)
        print(f"   R1251 header(32B) found in EE-RAM at: 0x{idx:08X}" if idx>=0 else "   R1251 header NOT found in EE-RAM")
        # Search portrait distinctive chunk in RAM
        ds=R1251[55552:55552+256]
        di=buf.find(ds)
        print(f"   R1251 distinctive portrait chunk found in EE-RAM at: 0x{di:08X}" if di>=0 else "   R1251 portrait pixels NOT found in EE-RAM (not loaded!)")

# Also the prompt mentions 0x509F8C holds 0x01A28EEC (CUR) — that's ptr-0x14. Dump the CG descriptor.
print("\nCG descriptor dump (CUR, around ptr):")
ptr=struct.unpack_from('<I',cur,CGSLOT)[0]
for o in range(-0x20,0x20,4):
    a=ptr+o
    if 0<=a<len(cur):
        print(f"   ptr{o:+#05x} (0x{a:08X}) = 0x{struct.unpack_from('<I',cur,a)[0]:08X}")
