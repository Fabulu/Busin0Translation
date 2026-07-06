import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
data=open("extracted/SLPM_653.78",'rb').read()
def va2off(va): return va-0x100000+0x80
lo,hi=0x305000,0x306000
LS={0x20:'lb',0x21:'lh',0x25:'lhu',0x29:'sh',0x23:'lw',0x2b:'sw'}
for va in range(lo,hi,4):
    o=va2off(va); w=struct.unpack('<I',data[o:o+4])[0]
    op=w>>26
    if op in LS:
        imm=w&0xffff
        if imm>=0x8000: imm-=0x10000
        if imm in (0x3c,0x3e,0x40):
            rt=(w>>16)&0x1f; base=(w>>21)&0x1f
            print(f"0x{va:08x}: {LS[op]:4s} rt={rt} off={imm:#x}(base={base})")
