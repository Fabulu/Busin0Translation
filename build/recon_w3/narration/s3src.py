import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
data=open("extracted/SLPM_653.78",'rb').read()
def va2off(va): return va-0x100000+0x80
# find writes to $s3 (reg 19) in 0x307da0..0x3098e0
lo,hi=0x307da0,0x3098e0
def dec(va,w):
    op=w>>26
    if op==0:
        fn=w&0x3f; rs=(w>>21)&0x1f; rt=(w>>16)&0x1f; rd=(w>>11)&0x1f
        if rd==19: return f"SPECIAL fn={fn:#x} rd=s3 rs={rs} rt={rt}"
    else:
        rt=(w>>16)&0x1f; rs=(w>>21)&0x1f; imm=w&0xffff
        if imm>=0x8000: imm-=0x10000
        if rt==19 and op in (0x09,0x0d,0x0f,0x20,0x21,0x23,0x24,0x25,0x37):
            nm={0x09:'addiu',0x0d:'ori',0x0f:'lui',0x20:'lb',0x21:'lh',0x23:'lw',0x24:'lbu',0x25:'lhu',0x37:'ld'}[op]
            return f"{nm} s3, {imm:#x}({rs})" if op>=0x20 else f"{nm} s3,{rs},{imm:#x}"
    return None
for va in range(lo,hi,4):
    o=va2off(va); w=struct.unpack('<I',data[o:o+4])[0]
    d=dec(va,w)
    if d: print(f"0x{va:08x}: {d}")
