import sys, json, struct
sys.stdout.reconfigure(encoding='utf-8')
# manifest gives offset/size in PACKDATA for each resource
man=json.load(open("C:/programmieren/wizardrytranslation/extracted/packdata_resources/manifest.json",encoding="utf-8"))
m=man[1197]
print("manifest[1197]:", {k:m[k] for k in m if k in ('offset','size','type_code','sector','skipped','name')})
off=m.get('offset'); size=m.get('size')
dig=open("C:/programmieren/wizardrytranslation/extracted/PACKDATA.DIG","rb")
if off is None:
    # maybe 'sector'
    sec=m.get('sector'); off=sec*2048 if sec is not None else None
print("offset used:", off, "size:", size)
dig.seek(off)
b=dig.read(size if size else 0x20000)
sec1=b[0x20:0x20+0x1FB8]
tgt=struct.unpack_from(">I",sec1,0x5D0+10)[0]
c=struct.unpack_from(">H",sec1,0x117E+4)[0]
print("ORIGINAL PACKDATA.DIG R1197: 0x06@5D0 target=0x%04X  0Cidx=0x%02X"%(tgt,c))
print("  -> %s"%("08AB = pristine target, 0x113 = pristine idx" if tgt==0x08AB else "0614!"))
print("first 0x20 header:", b[:0x20].hex())
