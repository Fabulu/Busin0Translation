import sys, json, binascii
sys.stdout.reconfigure(encoding='utf-8')
ee = open(r"C:/programmieren/wizardrytranslation/build/recon_tri/extract/requestbroken__ee.bin","rb").read()
opt=json.load(open(r"C:/programmieren/wizardrytranslation/build/recon_v85/exe-interpreter/opcode_table_v85.json"))["opcodes"]
res=0x011C3D00; sec1=res+0x20
s=ee[sec1:sec1+0x1FB8]
pre=open("C:/programmieren/wizardrytranslation/build/packdata_resources_backup/1197_type02.raw","rb").read()
sp=pre[0x20:0x20+0x1FB8]
def oplen(op):
    info=opt.get("0x%02X"%op); return (info["bytes"],info["note"]) if info else (2,"??")
# Walk Section1 from 0, find opcode boundaries, mark which opcode each diff falls in
boundaries=[]
a=0
while a < len(s)-1:
    op=(s[a]<<8)|s[a+1]
    ln,note=oplen(op)
    boundaries.append((a,op,ln,note))
    a+=ln
# index
def find_op(off):
    for (a,op,ln,note) in boundaries:
        if a<=off<a+ln: return (a,op,ln,note)
    return None
for off in [0x5DC, 0x1183, 0x13F3, 0x1EDF, 0x1F43, 0x1FA7]:
    b=find_op(off)
    if b:
        a,op,ln,note=b
        print("diff@%05X in opcode@%05X op=%02X len=%d [%s]"%(off,a,op,ln,note))
        print("   v99: %s"%s[a:a+ln].hex())
        print("   pre: %s"%sp[a:a+ln].hex())
