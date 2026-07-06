import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
D=open('extracted/SLPM_653.78','rb').read()
def v2f(va): return va-0x100000+0x80
def f2v(off): return off-0x80+0x100000
def word(va): return struct.unpack('<I',D[v2f(va):v2f(va)+4])[0]
# For each STORE to off 0x290, look at the 4 instrs before for ori/andi imm
stores=[0x2f2a9c,0x2f4810,0x2f4a38,0x2f96d4,0x2f9734,0x2f97a4,0x2f97b4,0x2f9888,0x2fa4f0,0x2fc6d0,0x2fc6e4,0x2fd780,0x2fd794,0x2fdf2c,0x2fdf74,0x2fe0fc,0x2fe20c,0x2fe254,0x2fe3dc,0x2fe4fc,0x2fe54c,0x2fe6dc,0x2fe9cc,0x2feb4c,0x2feba0]
for s in stores:
    # find preceding ori/andi within 3 instr
    info=''
    for k in range(1,4):
        w=word(s-4*k)
        op=w>>26
        if op==0x0d: # ori
            info='ori 0x%x'%(w&0xffff); break
        if op==0x0c: # andi
            info='andi 0x%x'%(w&0xffff); break
        if op==0x09 and ((w>>21)&0x1f)==0: # addiu rt,zero,imm (mask building)
            info='li 0x%x'%(w&0xffff)
    print('store %08x  %s'%(s,info))
