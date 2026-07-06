import sys, json, struct
sys.stdout.reconfigure(encoding='utf-8')
opt=json.load(open(r"C:/programmieren/wizardrytranslation/build/recon_v85/exe-interpreter/opcode_table_v85.json"))["opcodes"]
b=open("C:/programmieren/wizardrytranslation/build/recon_w2/parked/orig1197.raw","rb").read()
s=b[0x20:0x20+0x1FB8]
so=struct.unpack_from("<I",b,0x18)[0]; ss=struct.unpack_from("<I",b,0x14)[0]
sec2=b[so:so+ss]; words=[struct.unpack_from(">H",sec2,i*2)[0] for i in range(len(sec2)//2)]
# group boundaries by word idx
gstart=[0]; 
for i,w in enumerate(words):
    if w==0xFFFF and i+1<len(words): gstart.append(i+1)
def word_to_group(woff):
    import bisect
    g=bisect.bisect_right(gstart,woff)-1
    return g
def oplen(op):
    info=opt.get("0x%02X"%op); return info["bytes"] if info else 2
a=0
print("DISPLAY(0x04)/LABEL(0x14)/SEC2REF(0x0C,0x0D) -> group:")
while a<len(s)-1:
    op=(s[a]<<8)|s[a+1]; ln=oplen(op)
    if op==0x04 and a+10<=len(s):
        off=struct.unpack_from(">I",s,a+2)[0]; cnt=struct.unpack_from(">I",s,a+6)[0]
        if off<len(words):
            print("  S1+%05X 0x04 DISPLAY off=%d cnt=%d -> group %d"%(a,off,cnt,word_to_group(off)))
    elif op==0x14 and a+14<=len(s):
        off=struct.unpack_from(">I",s,a+6)[0]; cnt=struct.unpack_from(">I",s,a+10)[0]
        if off<len(words):
            print("  S1+%05X 0x14 LABEL off=%d cnt=%d -> group %d"%(a,off,cnt,word_to_group(off)))
    a+=ln
