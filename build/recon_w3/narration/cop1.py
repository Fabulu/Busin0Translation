import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
data=open("extracted/SLPM_653.78",'rb').read()
def va2off(va): return va-0x100000+0x80
# decode COP1 (op=0x11) and lwc1/swc1(0x31/0x39) manually
FMT={16:'s',17:'d',20:'w'}
COP1FN={0:'add',1:'sub',2:'mul',3:'div',4:'sqrt',5:'abs',6:'mov',7:'neg',
        0x24:'cvt.w',0x20:'cvt.s',0x21:'cvt.d',0x18:'adda',0x1c:'madd',0x9:'msub'}
def dec(va,w):
    op=w>>26
    if op==0x31: # lwc1
        ft=(w>>16)&0x1f; base=(w>>21)&0x1f; imm=w&0xffff
        if imm>=0x8000: imm-=0x10000
        return f"lwc1   $f{ft}, {imm:#x}(${base})"
    if op==0x39:
        ft=(w>>16)&0x1f; base=(w>>21)&0x1f; imm=w&0xffff
        if imm>=0x8000: imm-=0x10000
        return f"swc1   $f{ft}, {imm:#x}(${base})"
    if op==0x11:
        fmt=(w>>21)&0x1f; ft=(w>>16)&0x1f; fs=(w>>11)&0x1f; fd=(w>>6)&0x1f; fn=w&0x3f
        if fmt==8: # bc1
            return f"bc1{'t' if (ft&1) else 'f'} ..."
        if fmt==0: return f"mfc1   ${ft}, $f{fs}"  # rs field
        if fmt==4: return f"mtc1   ${ft}, $f{fs}"
        fm=FMT.get(fmt,str(fmt)); nm=COP1FN.get(fn,f"fn{fn:#x}")
        return f"{nm}.{fm} $f{fd},$f{fs},$f{ft}"
    return None
lo,hi=int(sys.argv[1],16),int(sys.argv[2],16)
for va in range(lo,hi,4):
    o=va2off(va); w=struct.unpack('<I',data[o:o+4])[0]
    d=dec(va,w)
    if d: print(f"0x{va:08x}: {w:08x}  {d}")
