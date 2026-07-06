import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
EXE='extracted/SLPM_653.78'; BASE=0x100000; FOFF=0x80
data=open(EXE,'rb').read()
# scan whole text for jal/j to target
def v2f(v): return v-BASE+FOFF
targets=[int(x,16) for x in sys.argv[1:]]
# text section assume from 0x100000.. file len
end=len(data)
for off in range(FOFF, end-4, 4):
    w=struct.unpack_from('<I',data,off)[0]
    op=w>>26
    if op in (2,3): # j / jal
        tgt=((off-FOFF+BASE)&0xF0000000)|((w&0x03FFFFFF)<<2)
        if tgt in targets:
            va=off-FOFF+BASE
            print("%-4s at 0x%08x -> 0x%08x"%('jal' if op==3 else 'j', va, tgt))
