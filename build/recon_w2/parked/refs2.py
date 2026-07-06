import sys, json, struct, bisect
sys.stdout.reconfigure(encoding='utf-8')
opt=json.load(open(r"C:/programmieren/wizardrytranslation/build/recon_v85/exe-interpreter/opcode_table_v85.json"))["opcodes"]
b=open("C:/programmieren/wizardrytranslation/build/recon_w2/parked/orig1197.raw","rb").read()
s=b[0x20:0x20+0x1FB8]
so=struct.unpack_from("<I",b,0x18)[0]; ss=struct.unpack_from("<I",b,0x14)[0]
sec2=b[so:so+ss]; words=[struct.unpack_from(">H",sec2,i*2)[0] for i in range(len(sec2)//2)]
gstart=[0]
for i,w in enumerate(words):
    if w==0xFFFF and i+1<len(words): gstart.append(i+1)
def wg(woff): return bisect.bisect_right(gstart,woff)-1
def oplen(op):
    info=opt.get("0x%02X"%op); return info["bytes"] if info else 2
# count opcode histogram and show 0x0C/0x0D/0x1A and any opcode referencing group index 1
a=0; hist={}
print("opcodes 0x0C/0x0D (idx@+4) and others that may ref groups:")
while a<len(s)-1:
    op=(s[a]<<8)|s[a+1]; ln=oplen(op); hist[op]=hist.get(op,0)+1
    if op in (0x0C,0x0D) and a+6<=len(s):
        idx=struct.unpack_from(">H",s,a+4)[0]
        # 0x0C idx is per the v99 note a channel bit, NOT group. show anyway
        pass
    a+=ln
print("opcode histogram (sorted by count):")
for op,c in sorted(hist.items(), key=lambda x:-x[1])[:25]:
    note=opt.get("0x%02X"%op,{}).get("note","??")
    print("  op=%02X x%d  %s"%(op,c,note[:40]))
