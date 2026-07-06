import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
EXE='C:/programmieren/wizardrytranslation/extracted/SLPM_653.78'
data=open(EXE,'rb').read()
def v2f(va): return va - 0x100000 + 0x80
def f2v(off): return off - 0x80 + 0x100000
va=int(sys.argv[1],16)
off=v2f(va)
# scan back: prologue addiu sp,sp,-N preceded by jr ra (end of prev fn)
prev_jr=False
for i in range(off, off-0x8000, -4):
    w=struct.unpack('<I',data[i:i+4])[0]
    op=w>>26; rs=(w>>21)&31; rt=(w>>16)&31; imm=w&0xffff
    if op==9 and rs==29 and rt==29 and (imm&0x8000):
        # check word before -8 (delay slot) area has jr ra somewhere just above
        print(f'candidate prologue 0x{f2v(i):08x}: addiu sp,sp,{imm-0x10000}')
        # only print first few
