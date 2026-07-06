import sys, json, struct
sys.stdout.reconfigure(encoding='utf-8')
opt=json.load(open(r"C:/programmieren/wizardrytranslation/build/recon_v85/exe-interpreter/opcode_table_v85.json"))["opcodes"]
s=open("C:/programmieren/wizardrytranslation/build/recon_w2/parked/orig1197.raw","rb").read()[0x20:0x20+0x1FB8]
def oplen(op):
    info=opt.get("0x%02X"%op); return (info["bytes"],info["note"]) if info else (2,"??")
# Walk from 0, record instruction starts, find which contains 0x1EF4
a=0; starts=[]
while a<len(s)-1:
    op=(s[a]<<8)|s[a+1]; ln,_=oplen(op)
    starts.append((a,op,ln)); a+=ln
# Is 0x1EF4 an instruction start?
inst_starts=set(x[0] for x in starts)
print("0x1EF4 is an instruction start?", 0x1EF4 in inst_starts)
# find enclosing
for (a,op,ln) in starts:
    if a<=0x1EF4<a+ln:
        print("0x1EF4 enclosing: opcode@%05X op=%02X len=%d bytes=%s"%(a,op,ln,s[a:a+ln].hex()))
# Print instructions from 0x1E80 to 0x1FC0
print("\n--- disasm 0x1E80..0x1FC0 ---")
for (a,op,ln) in starts:
    if 0x1E80<=a<=0x1FC0:
        _,note=oplen(op)
        print("  %05X: op=%02X %-12s %s"%(a,op,note[:12],s[a:a+ln].hex()))
