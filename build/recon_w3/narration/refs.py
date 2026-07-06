import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
data=open("extracted/SLPM_653.78",'rb').read()
def va2off(va): return va-0x100000+0x80
lo,hi=0x301000,0x309000
# find lw/lh/lbu/sw/sb with offset 0xa2 or 0xa6 (cell cursor) and 0xa0..0xa8
targets={0xa0,0xa2,0xa4,0xa6,0xa8}
LOAD_STORE={0x20:'lb',0x21:'lh',0x23:'lw',0x24:'lbu',0x25:'lhu',0x28:'sb',0x29:'sh',0x2b:'sw',
            0x31:'lwc1',0x39:'swc1'}
for va in range(lo,hi,4):
    o=va2off(va); w=struct.unpack('<I',data[o:o+4])[0]
    op=w>>26
    if op in LOAD_STORE:
        imm=w&0xffff
        if imm>=0x8000: imm-=0x10000
        if imm in targets:
            rt=(w>>16)&0x1f; base=(w>>21)&0x1f
            print(f"0x{va:08x}: {LOAD_STORE[op]:5s} rt={rt} off={imm:#x}(base={base})")
