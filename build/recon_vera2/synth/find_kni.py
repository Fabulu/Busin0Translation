import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open("C:/programmieren/wizardrytranslation/build/recon_tri/extract/veraisjapanese__ee.bin","rb").read()
# Find KNI-class second member. We know it's NOT in 0x55DD20 struct (that's Iris).
# Search for the class/level pattern. slot0 has 0x8000 header. Look for OTHER 0x80xx headers.
# Search every aligned u16 = 0x8000..0x8005 followed by name then FFFF.
print("scan for 0x80xx slot headers across RAM:")
i=0x300000; cnt=0
while i<len(ee)-8:
    v=struct.unpack_from('<H',ee,i)[0]
    if 0x8000<=v<=0x8005:
        # check name then FFFF within 16 bytes
        nm=[]; o=i+2
        ok=False
        while o<i+18:
            w=struct.unpack_from('<H',ee,o)[0]
            if w==0xFFFF: ok=len(nm)>0; break
            nm.append(w); o+=2
        if ok and 2<=len(nm)<=8:
            print(f"  @0x{i:X} hdr={v:#06x} name={nm}")
            cnt+=1
            if cnt>60: break
    i+=2
print("total",cnt)
