import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
exec(open(r"C:\programmieren\wizardrytranslation\build\_recon_2f2490\dec.py").read().split('start=0x2F2490')[0])
def dump(start,n=40,label=""):
    print(f"==== {label} {start:08X} ====")
    va=start
    for i in range(n):
        w=struct.unpack('<I',exe[va-VA_BASE:va-VA_BASE+4])[0]
        d=dec(w,va)
        print(f"{va:08X}  {d}")
        if d.startswith('jr $ra'):
            # print delay slot
            va+=4
            w=struct.unpack('<I',exe[va-VA_BASE:va-VA_BASE+4])[0]
            print(f"{va:08X}  {dec(w,va)}")
            break
        va+=4
for fn,lbl in [(0x2F1590,"gate getter A (0x4FE6AC)"),(0x2F15A0,"gate getter B (0x4FE68C)"),
               (0x2F15C0,"INPUT/EDGE getter"),(0x2F15F0,"selection/confirm fn"),
               (0x2F1E30,"cancel handler"),(0x2F2240,"sub 2f2240")]:
    dump(fn,40,lbl); print()
