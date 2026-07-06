import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
EXE='C:/programmieren/wizardrytranslation/extracted/SLPM_653.78'
data=open(EXE,'rb').read()
def f2v(off): return off - 0x80 + 0x100000
def v2f(va): return va - 0x100000 + 0x80
# find lui aX,0xHI ; addiu aX,aX,LO that form a target VA
target=int(sys.argv[1],16)
hi=(target>>16)&0xffff; lo=target&0xffff
# account for sign extension of addiu lo
if lo & 0x8000:
    hi=(hi+1)&0xffff
for off in range(0,len(data)-7,4):
    w=struct.unpack('<I',data[off:off+4])[0]
    op=w>>26; rt=(w>>16)&31; imm=w&0xffff
    if op==0x0f and imm==hi: # lui rt,hi
        # scan a few instrs forward for addiu rt,rt,lo
        for j in range(off+4, off+0x40, 4):
            w2=struct.unpack('<I',data[j:j+4])[0]
            op2=w2>>26; rs2=(w2>>21)&31; rt2=(w2>>16)&31; imm2=w2&0xffff
            if op2==9 and rs2==rt and rt2==rt and imm2==lo:
                print(f'0x{f2v(off):08x}: lui r{rt},0x{hi:04x} ... 0x{f2v(j):08x}: addiu r{rt},r{rt},0x{lo:04x}  -> 0x{target:08x}')
                break
