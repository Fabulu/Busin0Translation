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
dump(0x2F3330,80,"cursor mover 2F3330")
