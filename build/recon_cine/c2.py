import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
exe=open("extracted/SLPM_653.78","rb").read()
for tgt in (0x30B000,0x30B210,0x30B3F0,0x30B770):
    jt=(tgt>>2)&0x3FFFFFF; rs=[]
    for off in range(0x80,len(exe)-4,4):
        w=struct.unpack_from("<I",exe,off)[0]
        if (w>>26)==3 and (w&0x3FFFFFF)==jt: rs.append(0x100000+off-0x80)
    print(f"callers of 0x{tgt:08X}: "+", ".join(f"0x{v:08X}" for v in rs))
