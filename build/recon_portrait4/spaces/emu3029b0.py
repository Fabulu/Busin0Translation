import sys, struct, rabbitizer
sys.stdout.reconfigure(encoding='utf-8')
exe=open('extracted/SLPM_653.78','rb').read()
BASE=0xFFF80
# Statically map the dispatch of func_3029B0: it's a chain of `ori v0,zero,CONST; beq v1,v0,TARGET`
# v1 = glyph. Find all (const, target) and the final fallthrough.
va=0x3029B0
pc=va
end=va+0x340
pairs=[]
last_ori=None
fallthrough=None
while pc<end:
    raw=struct.unpack_from('<I',exe,pc-BASE)[0]
    op=(raw>>26)&0x3F
    # ori rt,zero,imm  -> op=0x0D, rs=0
    if op==0x0D and ((raw>>21)&0x1F)==0 and ((raw>>16)&0x1F)==2:
        last_ori=raw&0xFFFF
    # beq v1(=3),v0(=2)  op=4 rs=3 rt=2
    if op==0x04 and ((raw>>21)&0x1F)==3 and ((raw>>16)&0x1F)==2:
        imm=raw&0xFFFF
        if imm>=0x8000: imm-=0x10000
        tgt=pc+4+imm*4
        pairs.append((last_ori,tgt,pc))
    # unconditional b (beq zero,zero) op=4 rs=0 rt=0 -> the fallthrough jump
    if op==0x04 and ((raw>>21)&0x1F)==0 and ((raw>>16)&0x1F)==0:
        imm=raw&0xFFFF
        if imm>=0x8000: imm-=0x10000
        t=pc+4+imm*4
        # the big fallthrough is the one jumping far forward
        if abs(imm)>0x40:
            fallthrough=(t,pc)
    pc+=4
print("dispatch pairs (glyph_const -> handler_va):")
for c,t,at in pairs:
    print(f"  glyph==0x{c:04X} -> 0x{t:X}  (beq@0x{at:X})")
print("fallthrough (normal glyph) ->",hex(fallthrough[0]) if fallthrough else None, "from",hex(fallthrough[1]) if fallthrough else None)
