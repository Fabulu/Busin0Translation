import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
exec(open(r"C:\programmieren\wizardrytranslation\build\_recon_2f2490\dec.py").read().split('start=0x2F2490')[0])
def dump(start,n,label="",stopjr=True):
    print(f"==== {label} {start:08X} ====")
    va=start
    for i in range(n):
        w=struct.unpack('<I',exe[va-VA_BASE:va-VA_BASE+4])[0]
        d=dec(w,va); print(f"{va:08X}  {d}")
        if stopjr and d.startswith('jr $ra'):
            va+=4; w=struct.unpack('<I',exe[va-VA_BASE:va-VA_BASE+4])[0]; print(f"{va:08X}  {dec(w,va)}"); break
        va+=4
# interpreter dispatcher 0x2F3230 (per CLAUDE this is the opcode dispatcher; but here called as menu tick). show first chunk
dump(0x2F3230,60,"interp/menu-tick 2F3230")
