import sys,struct
sys.path.insert(0,'build/_recon_2f2490')
from dec import dec
EXE=r"C:\programmieren\wizardrytranslation\extracted\SLPM_653.78"
exe=open(EXE,'rb').read()
VA_BASE=0xFFF80
def disrange(start,end):
    pc=start
    while pc<end:
        fo=pc-VA_BASE
        w=struct.unpack_from('<I',exe,fo)[0]
        print(f"{pc:08X}: {w:08X}  {dec(w,pc)}")
        pc+=4
if __name__=='__main__':
    s=int(sys.argv[1],16); e=int(sys.argv[2],16); disrange(s,e)
