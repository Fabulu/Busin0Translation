import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
EXE=r"C:\programmieren\wizardrytranslation\extracted\SLPM_653.78"
VA_BASE=0xFFF80
exe=open(EXE,'rb').read()
exec(open(r"C:\programmieren\wizardrytranslation\build\_recon_2f2490\dec.py").read().split("start=0x2F2490")[0])
import sys as _s
start=int(_s.argv[1],16); end=int(_s.argv[2],16)
va=start
while va<=end:
    fo=va-VA_BASE
    w=struct.unpack('<I',exe[fo:fo+4])[0]
    print(f"{va:08X} (fo {fo:06X})  {w:08X}  {dec(w,va)}")
    va+=4
