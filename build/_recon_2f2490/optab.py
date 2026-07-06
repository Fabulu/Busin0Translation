import struct,sys
sys.stdout.reconfigure(encoding='utf-8')
EXE=r"C:\programmieren\wizardrytranslation\extracted\SLPM_653.78"
VA_BASE=0xFFF80
exe=open(EXE,'rb').read()
TAB=0x4C9360
ents=[]
for i in range(193):
    h=struct.unpack('<I',exe[TAB-VA_BASE+i*4:TAB-VA_BASE+i*4+4])[0]
    ents.append((i,h))
# given a query VA, find which opcode handler range it's in
import bisect
sh=sorted(set(h for _,h in ents if h>0x2F0000 and h<0x310000))
def owner(va):
    # find largest handler start <= va
    cand=[h for h in sh if h<=va]
    if not cand: return None
    h=max(cand)
    ops=[i for i,hh in ents if hh==h]
    return h,ops
for q in [0x2F4810,0x2F4A38,0x2F96D4,0x2F97A4,0x2F9888,0x2FA0E8,0x2FA4F0,0x2FA584,0x2FC68C,0x2FC6D0,0x2FC71C,0x2FD780,0x2FDF2C,0x2FE4FC]:
    o=owner(q)
    if o:
        h,ops=o
        print(f"{q:08X} in handler {h:08X} opcodes {[hex(x) for x in ops]}")
print("--- handler table (op->handler), unique ---")
seen={}
for i,h in ents:
    seen.setdefault(h,[]).append(i)
for h in sorted(seen):
    if 0x2F0000<h<0x310000:
        print(f"{h:08X}: ops {[hex(x) for x in seen[h]]}")
