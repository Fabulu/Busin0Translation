import sys, glob, struct, os
sys.stdout.reconfigure(encoding='utf-8')
# Find EVERY 1197_type02.raw and the original PACKDATA extraction sources
paths=glob.glob("C:/programmieren/wizardrytranslation/**/1197_type02.raw", recursive=True)
for p in sorted(set(paths)):
    try:
        b=open(p,"rb").read()
        if len(b)<0x5E0: 
            print(p,"too small"); continue
        sec1=b[0x20:0x20+0x1FB8]
        tgt=struct.unpack_from(">I",sec1,0x5D0+10)[0]
        # also the 0x0C@117E low byte
        c=struct.unpack_from(">H",sec1,0x117E+4)[0]
        sec2sz=struct.unpack_from("<I",b,0x14)[0]
        mt=os.path.getmtime(p)
        print("%-70s tgt=0x%04X 0Cidx=0x%02X sec2sz=0x%X size=%d"%(p.replace("C:/programmieren/wizardrytranslation/",""),tgt,c,sec2sz,len(b)))
    except Exception as e:
        print(p,"ERR",e)
