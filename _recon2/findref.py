import sys, struct
from capstone import *
sys.stdout.reconfigure(encoding='utf-8')
EXE=r'C:\programmieren\wizardrytranslation\extracted\SLPM_653.78'
def v2f(va): return va - 0x100000 + 0x80
def f2v(off): return off + 0x100000 - 0x80
data=open(EXE,'rb').read()
target=int(sys.argv[1],16)
hi=target>>16; lo=target&0xFFFF
# Find lui reg,hi  then addiu reg,reg,lo composing target
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS64 | CS_MODE_LITTLE_ENDIAN)
# search as raw data word (LE)
needle=struct.pack('<I',target)
i=0
print("as data word:")
while True:
    j=data.find(needle,i)
    if j<0: break
    print(f"  file 0x{j:X} -> VA 0x{f2v(j):08X}")
    i=j+1
# search lui+addiu pair (account for hi+1 if lo>=0x8000)
hi_adj=hi + (1 if lo>=0x8000 else 0)
print(f"\nlui/addiu pairs (hi={hi:#x} or {hi_adj:#x}, lo={lo:#x} signed):")
for va in range(0x100000, f2v(len(data)-8),4):
    o=v2f(va)
    if o+8>len(data): break
    a=list(md.disasm(data[o:o+4],va))
    b=list(md.disasm(data[o+4:o+8],va+4))
    if a and b and a[0].mnemonic=='lui' and b[0].mnemonic=='addiu':
        try:
            ah=int(a[0].op_str.split(',')[1],16)
            br=b[0].op_str.split(',')
            if len(br)==3:
                bl=int(br[2],16)&0xFFFF
                full=(ah<<16)+struct.unpack('<h',struct.pack('<H',bl))[0]
                if full==target:
                    print(f"  0x{va:08X}: {a[0].op_str} ; {b[0].op_str}")
        except: pass
