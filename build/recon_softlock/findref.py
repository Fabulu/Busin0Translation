import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
data=open('extracted/SLPM_653.78','rb').read()
base=0x100000; hdr=0x80
def va_at(o): return o-hdr+base
target=int(sys.argv[1],16)
hi=(target>>16)&0xffff; lo=target&0xffff
# account for sign-extension of lo: if lo>=0x8000, hi in lui must be hi+1
hi_adj = hi + (1 if lo>=0x8000 else 0)
slo = lo if lo<0x8000 else lo-0x10000
# scan for lui reg,hi_adj followed (within 8 instr) by addiu/ori reg,reg,lo
print(f"target=0x{target:08X} hi_adj=0x{hi_adj:04X} lo=0x{lo:04X} (signed {slo})")
n=len(data)
for o in range(hdr, n-4, 4):
    w=struct.unpack('<I',data[o:o+4])[0]
    op=w>>26
    if op==0x0F: # lui
        rt=(w>>16)&0x1f; imm=w&0xffff
        if imm==hi_adj:
            # look ahead
            for j in range(1,10):
                o2=o+j*4
                w2=struct.unpack('<I',data[o2:o2+4])[0]
                op2=w2>>26; rs=(w2>>21)&0x1f; rt2=(w2>>16)&0x1f; imm2=w2&0xffff
                if op2 in (0x09,0x0D) and rs==rt:  # addiu or ori
                    if (op2==0x09 and imm2==lo) or (op2==0x0D and imm2==lo):
                        print(f"  ref @VA 0x{va_at(o):08X} (lui) + @0x{va_at(o2):08X}")
                        break
