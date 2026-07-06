import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open("C:/programmieren/wizardrytranslation/build/recon_tri/extract/veraisjapanese__ee.bin","rb").read()
pris=open("C:/programmieren/wizardrytranslation/extracted/packdata_raw/1892_type20.raw",'rb').read()
REC_BASE=0x140; REC_STRIDE=0x130
A_BASE=0x55DD20; A_STRIDE=0x1F0
# Map array A slots 1..5 to R1892 records. slot1=Iris=rec0. Check each.
print("Array A name field (bytes at +2..FFFF) vs R1892 record name field:")
for aslot in range(1,6):
    a_off=A_BASE+aslot*A_STRIDE+2
    # read A name bytes until FFFF
    o=a_off; 
    while struct.unpack_from('<H',ee,o)[0]!=0xFFFF: o+=2
    a_bytes=ee[a_off:o+2]
    # find matching R1892 record
    found=None
    for rec in range(20):
        r_off=REC_BASE+rec*REC_STRIDE+2
        ro=r_off
        while struct.unpack_from('<H',pris,ro)[0]!=0xFFFF: ro+=2
        r_bytes=pris[r_off:ro+2]
        if r_bytes==a_bytes:
            found=rec; break
    print(f"  A-slot{aslot} name={a_bytes.hex()} -> R1892 rec{found}" + (" VERBATIM MATCH" if found is not None else " NO MATCH"))
