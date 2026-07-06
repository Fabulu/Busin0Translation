import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
EXE='extracted/SLPM_653.78'; BASE=0x100000; FOFF=0x80
data=open(EXE,'rb').read()
def v2f(v): return v-BASE+FOFF
# walk backward to find addiu $sp,$sp,-N (271bdXXXX) = func prologue
va=int(sys.argv[1],16)
o=v2f(va)
for k in range(o,o-0x2000,-4):
    w=struct.unpack_from('<I',data,k)[0]
    if (w>>16)==0x27bd and (w&0xffff)>=0x8000: # addiu sp,sp,neg
        print("func start ~0x%08x  (%08x)"%(k-FOFF+BASE,w)); break
