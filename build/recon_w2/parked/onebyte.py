import sys, json, struct
sys.stdout.reconfigure(encoding='utf-8')
opt=json.load(open(r"C:/programmieren/wizardrytranslation/build/recon_v85/exe-interpreter/opcode_table_v85.json"))["opcodes"]
iso=open(r"C:/programmieren/wizardrytranslation/Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso","rb").read()
sig=bytes.fromhex("000000001fb800002000000000000000010000005c0e010040b80000")
idx=iso.find(sig)
orig=iso[idx:idx+0x20000]
s=orig[0x20:0x20+0x1FB8]
def oplen(op):
    info=opt.get("0x%02X"%op); return (info["bytes"],info["note"]) if info else (2,"??")
# walk to find opcode containing 0x10F5
a=0
while a<len(s)-1:
    op=(s[a]<<8)|s[a+1]; ln,note=oplen(op)
    if a<=0x10F5<a+ln:
        print("byte 0x10F5 in opcode@%05X op=%02X len=%d [%s]"%(a,op,ln,note))
        print("  orig bytes:", s[a:a+ln].hex())
        v99=open("C:/programmieren/wizardrytranslation/build/patched_type2/1197_type02.raw","rb").read()[0x20:0x20+0x1FB8]
        print("  v99  bytes:", v99[a:a+ln].hex())
        break
    a+=ln
