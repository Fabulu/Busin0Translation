import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
EXE='extracted/SLPM_653.78'; BASE=0x100000; FOFF=0x80
data=open(EXE,'rb').read()
def v2f(v): return v-BASE+FOFF
for off in range(FOFF,len(data)-4,4):
    w=struct.unpack_from('<I',data,off)[0]
    if (w>>26)==0x29 and (w&0xffff)==0x298: # sh ..,0x298(base)
        rt=(w>>16)&31
        # check preceding 8 instrs for 'addiu rt,zero,-1'
        for back in range(1,6):
            pw=struct.unpack_from('<I',data,off-back*4)[0]
            if (pw>>26)==9 and ((pw>>16)&31)==rt and ((pw>>21)&31)==0 and (pw&0xffff)==0xffff:
                print("CLEAR 0x298=-1 at 0x%08x (rt=%d)"%(off-FOFF+BASE,rt))
                break
