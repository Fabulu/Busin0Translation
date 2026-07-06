import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
EXE=r"C:\programmieren\wizardrytranslation\extracted\SLPM_653.78"
VA_BASE=0xFFF80
exe=open(EXE,'rb').read()
target=int(sys.argv[1],16)
hi=(target>>16)&0xFFFF
lo=target&0xFFFF
# adjust for sign-extension of lo: if lo>=0x8000, lui uses hi+1
if lo>=0x8000: hi_adj=(hi+1)&0xFFFF
else: hi_adj=hi
n=len(exe)
# search for literal 32-bit little-endian word == target (pointer table)
tb=struct.pack('<I',target)
print(f"target 0x{target:X}: lui needs imm {hi_adj:04X}, ori/addiu lo {lo:04X}")
print("== literal word (function-pointer table) ==")
for fo in range(0, n-3, 4):
    if exe[fo:fo+4]==tb:
        print(f"  ptr @ VA {fo+VA_BASE:08X} (fo {fo:06X})")
print("== lui $r, hi_adj  followed within 8 instr by ori/addiu lo ==")
luis=[]
for fo in range(0, n-3, 4):
    w=struct.unpack('<I',exe[fo:fo+4])[0]
    op=(w>>26)&0x3F; rt=(w>>16)&0x1F; imm=w&0xFFFF
    if op==0x0F and imm==hi_adj:
        luis.append((fo,rt))
for fo,rt in luis:
    for d in range(1,9):
        f2=fo+d*4
        if f2+4>n: break
        w2=struct.unpack('<I',exe[f2:f2+4])[0]
        op2=(w2>>26)&0x3F; rs2=(w2>>21)&0x1F; imm2=w2&0xFFFF
        if (op2==0x0D or op2==0x09) and imm2==lo and rs2==rt:
            print(f"  lui@{fo+VA_BASE:08X} + lo@{f2+VA_BASE:08X}  -> 0x{target:X}")
            break
