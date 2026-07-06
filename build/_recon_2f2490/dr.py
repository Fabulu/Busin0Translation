import sys,struct
sys.path.insert(0,'build/_recon_2f2490')
from dec import dec
EXE=r"C:\programmieren\wizardrytranslation\extracted\SLPM_653.78"
VA_BASE=0xFFF80
exe=open(EXE,'rb').read()
def fo(va): return va-0x100000+0x80
start=int(sys.argv[1],16); end=int(sys.argv[2],16)
va=start
while va<end:
    off=fo(va)
    w=struct.unpack_from('<I',exe,off)[0]
    print("%08X: %08X  %s"%(va,w,dec(w,va)))
    va+=4
