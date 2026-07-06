import struct,sys
sys.stdout.reconfigure(encoding='utf-8')
EXE=r"C:\programmieren\wizardrytranslation\extracted\SLPM_653.78"
VA_BASE=0xFFF80
exe=open(EXE,'rb').read()
# Search whole interpreter region for sw/sh/sb to offsets 0x290, 0x298, 0x29e, 0x2a0, 0x2a6, 0x2a7
# store ops: sw=0x2B, sh=0x29, sb=0x28 ; we want imm in target set
targets={0x290:'+0x290(flag)',0x298:'+0x298(nameidx)',0x29e:'+0x29e',0x2a0:'+0x2a0',0x2a6:'+0x2a6',0x2a7:'+0x2a7'}
start=0x2F0000; end=0x300000
va=start
while va<end:
    w=struct.unpack('<I',exe[va-VA_BASE:va-VA_BASE+4])[0]
    op=(w>>26)&0x3F; rs=(w>>21)&0x1F; rt=(w>>16)&0x1F
    imm=w&0xFFFF; s=imm-0x10000 if imm&0x8000 else imm
    if op in (0x2B,0x29,0x28) and s in targets:
        nm={0x2B:'sw',0x29:'sh',0x28:'sb'}[op]
        print(f"{va:08X}  {nm} rt={rt} {s:#x}(rs={rs}) -> {targets[s]}")
    va+=4
