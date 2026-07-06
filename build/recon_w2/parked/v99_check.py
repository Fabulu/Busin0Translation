import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
for name,path in [("patched_type2(v99)","build/patched_type2/1197_type02.raw"),
                  ("packdata_resources(v99)","build/packdata_resources/1197_type02.raw"),
                  ("backup(pristine)","build/packdata_resources_backup/1197_type02.raw")]:
    b=open("C:/programmieren/wizardrytranslation/"+path,"rb").read()
    sec1=b[0x20:0x20+0x1FB8]
    op=sec1[0x5D0:0x5D0+14]
    tgt=struct.unpack_from(">I",op,10)[0]
    print(f"{name}: 0x06@5D0 = {op.hex()}  target=0x{tgt:04X}  {'CORRUPT' if tgt==0x0614 else ('PRISTINE' if tgt==0x08AB else '???')}")
