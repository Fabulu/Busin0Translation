import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
EXE=r"C:\programmieren\wizardrytranslation\extracted\SLPM_653.78"
VA_BASE=0xFFF80
exe=open(EXE,'rb').read()
REG=["zero","at","v0","v1","a0","a1","a2","a3","t0","t1","t2","t3","t4","t5","t6","t7","s0","s1","s2","s3","s4","s5","s6","s7","t8","t9","k0","k1","gp","sp","s8","ra"]
# loads from off 0x290 : lw=0x23 lh=0x21 lhu=0x25 lb=0x20 lbu=0x24
for off in (0x290,):
    print(f"=== loads of +{off:#x} (in 0x2F0000-0x2FF000 range) ===")
    for fo in range(0,len(exe)-4,4):
        w=struct.unpack('<I',exe[fo:fo+4])[0]
        op=(w>>26)&0x3F; imm=w&0xFFFF
        if op in (0x20,0x21,0x23,0x24,0x25) and imm==off:
            va=fo+VA_BASE
            if 0x2F0000<=va<=0x300000:
                rs=(w>>21)&0x1F; rt=(w>>16)&0x1F
                mn={0x20:'lb',0x21:'lh',0x23:'lw',0x24:'lbu',0x25:'lhu'}[op]
                print(f"  {va:08X}  {mn} ${REG[rt]},{off:#x}(${REG[rs]})")
