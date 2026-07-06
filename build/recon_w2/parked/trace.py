import sys, os, json, glob, struct
sys.stdout.reconfigure(encoding='utf-8')
# pristine source used by build
raw="C:/programmieren/wizardrytranslation/extracted/packdata_raw"
cands=glob.glob(raw+"/*1197*")
print("pristine raw candidates:", cands)
p=open(cands[0],"rb").read()
sec1=p[0x20:0x20+0x1FB8]
tgt=struct.unpack_from(">I",sec1,0x5D0+10)[0]
print("PRISTINE extracted/packdata_raw 0x06@5D0 target = 0x%04X (%s)"%(tgt,"08AB pristine" if tgt==0x08AB else "CORRUPT"))
