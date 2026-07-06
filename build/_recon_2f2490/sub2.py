import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
exec(open(r"C:\programmieren\wizardrytranslation\build\_recon_2f2490\dec.py").read().split('start=0x2F2490')[0])
def dump(start,n=60,label=""):
    print(f"==== {label} {start:08X} ====")
    va=start
    for i in range(n):
        w=struct.unpack('<I',exe[va-VA_BASE:va-VA_BASE+4])[0]
        d=dec(w,va)
        print(f"{va:08X}  {d}")
        if d.startswith('jr $ra'):
            va+=4
            w=struct.unpack('<I',exe[va-VA_BASE:va-VA_BASE+4])[0]
            print(f"{va:08X}  {dec(w,va)}")
            break
        va+=4
for fn,lbl,n in [(0x131D20,"early-exit gate (2F24D8)",40),
               (0x495E00,"495E00 (200-bit confirm?)",30),
               (0x494D80,"494D80 (1000 L?)",30),
               (0x18D9C0,"18D9C0 (4000 R?)",30),
               (0x30C920,"30C920 (lui2 X?)",30),
               (0x30B210,"30B210 (80 bit)",30)]:
    dump(fn,n,lbl); print()
