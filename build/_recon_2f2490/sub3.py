import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
exec(open(r"C:\programmieren\wizardrytranslation\build\_recon_2f2490\dec.py").read().split('start=0x2F2490')[0])
def dump(start,n,label=""):
    print(f"==== {label} {start:08X} ====")
    va=start
    for i in range(n):
        w=struct.unpack('<I',exe[va-VA_BASE:va-VA_BASE+4])[0]
        d=dec(w,va); print(f"{va:08X}  {d}")
        if d.startswith('jr $ra'):
            va+=4; w=struct.unpack('<I',exe[va-VA_BASE:va-VA_BASE+4])[0]; print(f"{va:08X}  {dec(w,va)}"); break
        va+=4
# 0x2ED5E0 (top, returns a1), 0x309870 (unconditional), 0x2F3450 (unconditional), 0x30B840, 0x30CBE0
for fn,lbl,n in [(0x2ED5E0,"top fn (a1=ret)",18),(0x309870,"uncond 309870 (a0,a1,a2=c8)",60),
                 (0x2F3450,"uncond 2F3450(a0)",60)]:
    dump(fn,n,lbl); print()
