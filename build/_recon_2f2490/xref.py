import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
EXE=r"C:\programmieren\wizardrytranslation\extracted\SLPM_653.78"
VA_BASE=0xFFF80
exe=open(EXE,'rb').read()
n=len(exe)
def refs_to(target):
    hi=(target>>16)&0xFFFF; lo=target&0xFFFF
    hi_adj=(hi+1)&0xFFFF if lo>=0x8000 else hi
    out=[]
    jalw=(0x03<<26)|((target>>2)&0x03FFFFFF); jw=(0x02<<26)|((target>>2)&0x03FFFFFF)
    tb=struct.pack('<I',target)
    luis=[]
    for fo in range(0,n-3,4):
        w=struct.unpack('<I',exe[fo:fo+4])[0]
        if w==jalw: out.append(("JAL",fo+VA_BASE))
        elif w==jw: out.append(("J",fo+VA_BASE))
        elif exe[fo:fo+4]==tb: out.append(("PTR",fo+VA_BASE))
        op=(w>>26)&0x3F; rt=(w>>16)&0x1F; imm=w&0xFFFF
        if op==0x0F and imm==hi_adj: luis.append((fo,rt))
    for fo,rt in luis:
        for d in range(1,9):
            f2=fo+d*4
            if f2+4>n: break
            w2=struct.unpack('<I',exe[f2:f2+4])[0]
            op2=(w2>>26)&0x3F; rs2=(w2>>21)&0x1F; imm2=w2&0xFFFF
            if (op2==0x0D or op2==0x09) and imm2==lo and rs2==rt:
                out.append(("LUI+LO",fo+VA_BASE)); break
    return out
for t in sys.argv[1:]:
    tv=int(t,16)
    print(f"== refs to 0x{tv:X} ==")
    for k,va in refs_to(tv): print(f"   {k} @ {va:08X}")
