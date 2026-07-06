import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
EXE='extracted/SLPM_653.78'
data=open(EXE,'rb').read()
def v2f(va): return va-0xFFF80
va=int(sys.argv[1],16)
# scan backwards for 'jr ra' followed by addiu sp,sp,-X (function prologue) OR addiu sp,sp,-X preceded by jr ra
off=v2f(va)
# find nearest prior 'addiu sp,sp,-imm' that follows a 'jr ra'/nop boundary
prev_jr=None
for o in range(off, off-0x6000, -4):
    w=struct.unpack_from('<I',data,o)[0]
    op=w>>26; rs=(w>>21)&31; rt=(w>>16)&31; imm=w&0xFFFF
    if op==9 and rs==29 and rt==29 and imm>=0x8000: # addiu sp,sp,-X
        print('prologue at 0x%08X  addiu sp,sp,-0x%X'%(o+0xFFF80, 0x10000-imm))
        break
