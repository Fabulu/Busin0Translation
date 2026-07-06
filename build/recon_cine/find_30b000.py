import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
exe=open("extracted/SLPM_653.78","rb").read()
# JAL to 0x30B000
jt=(0x30B000>>2)&0x3FFFFFF
jals=[]
ptrs=[]
for off in range(0x80,len(exe)-4,4):
    w=struct.unpack_from("<I",exe,off)[0]
    if (w>>26)==3 and (w&0x3FFFFFF)==jt: jals.append(0x100000+off-0x80)
    if w==0x0030B000: ptrs.append(0x100000+off-0x80)  # address as data
# also the func at 0x30B000 actually starts at 0x30AFF0? check prologue
print("prologue check 0x30AFF0:")
for va in (0x30AFE0,0x30AFF0,0x30B000):
    w=struct.unpack_from("<I",exe,va-0x100000+0x80)[0]
    print(f"  0x{va:08X}: {w:08X}")
print("JAL 0x30B000:", [f"0x{v:08X}" for v in jals])
print("data ptr ==0x0030B000:", [f"0x{v:08X}" for v in ptrs])
