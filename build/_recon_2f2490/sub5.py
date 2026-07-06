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
def find_start(va):
    a=va
    while a>va-0x800:
        w=struct.unpack('<I',exe[a-VA_BASE:a-VA_BASE+4])[0]
        if (w>>26)==9 and ((w>>21)&0x1f)==29 and ((w>>16)&0x1f)==29 and (w&0x8000):
            return a
        a-=4
    return va-0x40
s=find_start(0x2F2A9C)
print("fn start ~",hex(s))
dump(s,90,"fn(+290<-0)")
