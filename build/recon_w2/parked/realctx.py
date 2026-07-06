import sys, struct, json
sys.stdout.reconfigure(encoding='utf-8')
ee=open(r"C:/programmieren/wizardrytranslation/build/recon_tri/extract/requestbroken__ee.bin","rb").read()
opt=json.load(open(r"C:/programmieren/wizardrytranslation/build/recon_v85/exe-interpreter/opcode_table_v85.json"))["opcodes"]
def u32(a): return struct.unpack_from("<I",ee,a)[0]
sec1=0x011C3D20; sec2=0x011CF540
# Build set of valid instruction boundaries in v96 RAM R1197 sec1
res=0x011C3D00
s1=ee[res+0x20:res+0x20+0x1FB8]
def oplen(op):
    info=opt.get("0x%02X"%op); return info["bytes"] if info else 2
bounds=set(); a=0
while a<len(s1)-1:
    bounds.add(a); op=(s1[a]<<8)|s1[a+1]; a+=oplen(op)
# scan for ctx: pc field in sec1, AND pc-rel is a valid boundary
print("candidates with pc at a VALID instruction boundary:")
for a in range(0x00100000,0x02000000,4):
    v=u32(a)
    if sec1<=v<sec1+0x1FB8:
        rel=v-sec1
        if rel in bounds:
            # check structure: this is likely the live ctx
            flags=u32(a+0x290) if a+0x294<len(ee) else 0
            print("  ctx@%08X pc-rel=%05X flags@+290=%08X cnt@+29C=%04X"%(a,rel,flags,struct.unpack_from('<H',ee,a+0x29c)[0] if a+0x29e<len(ee) else 0))
