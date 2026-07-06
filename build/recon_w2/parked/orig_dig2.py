import sys, json, struct
sys.stdout.reconfigure(encoding='utf-8')
man=json.load(open("C:/programmieren/wizardrytranslation/extracted/packdata_resources/manifest.json",encoding="utf-8"))
m=man[1197]
off=m['sector_offset']*2048
size=m['sector_count']*2048
dig=open("C:/programmieren/wizardrytranslation/extracted/PACKDATA.DIG","rb")
dig.seek(off); b=dig.read(size)
print("header:", b[:0x20].hex())
sec1=b[0x20:0x20+0x1FB8]
tgt=struct.unpack_from(">I",sec1,0x5D0+10)[0]
c=struct.unpack_from(">H",sec1,0x117E+4)[0]
print("ORIGINAL extracted/PACKDATA.DIG R1197: 0x06@5D0 target=0x%04X  0Cidx=0x%02X"%(tgt,c))
# Also from the Japanese ISO directly? PACKDATA in ISO. We trust extracted/PACKDATA.DIG (839661568 = orig size).
