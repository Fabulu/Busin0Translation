import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
EXE='extracted/SLPM_653.78'; BASE=0x100000; FOFF=0x80
data=open(EXE,'rb').read()
def v2f(v): return v-BASE+FOFF
TBL=0x4C9360; N=193
tbl=[]
for i in range(N):
    h=struct.unpack_from('<I',data,v2f(TBL)+i*4)[0]
    tbl.append(h)
look=[int(x,16) for x in sys.argv[1:]] if len(sys.argv)>1 else []
for i,h in enumerate(tbl):
    if not look or h in look:
        print("opcode 0x%02X -> handler 0x%08x"%(i,h))
