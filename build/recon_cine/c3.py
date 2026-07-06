import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
exe=open("extracted/SLPM_653.78","rb").read()
def callers(tgt):
    jt=(tgt>>2)&0x3FFFFFF; r=[]
    for off in range(0x80,len(exe)-4,4):
        w=struct.unpack_from("<I",exe,off)[0]
        if (w>>26)==3 and (w&0x3FFFFFF)==jt: r.append(0x100000+off-0x80)
    return r
for t in (0x30AFF0,0x30B070,0x30B120):
    print(f"callers of 0x{t:08X}: "+", ".join(f"0x{v:08X}" for v in callers(t)))
