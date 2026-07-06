import struct,sys
sys.stdout.reconfigure(encoding='utf-8')
EXE=r"C:\programmieren\wizardrytranslation\extracted\SLPM_653.78"
VA_BASE=0xFFF80
exe=open(EXE,'rb').read()
# search interpreter region 0x2F3200..0x300000 for sh/sw/lh with given imm offset on any reg
target=int(sys.argv[1],16)  # e.g 0x298
want_store=sys.argv[2] if len(sys.argv)>2 else 'both'
start=0x2F3200; end=0x300000
for va in range(start,end,4):
    w=struct.unpack('<I',exe[va-VA_BASE:va-VA_BASE+4])[0]
    op=(w>>26)&0x3F; rs=(w>>21)&0x1F; rt=(w>>16)&0x1F
    imm=w&0xFFFF; s=imm-0x10000 if imm&0x8000 else imm
    if s==target:
        # sw=0x2B sh=0x29 sb=0x28 lw=0x23 lh=0x21 lhu=0x25
        kind={0x2B:'sw',0x29:'sh',0x28:'sb',0x23:'lw',0x21:'lh',0x25:'lhu',0x24:'lbu',0x20:'lb'}.get(op)
        if kind:
            print(f"{va:08X}  {kind} rt={rt} rs={rs} off={s:#x}")
