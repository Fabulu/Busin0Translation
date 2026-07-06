import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
D=open('extracted/SLPM_653.78','rb').read()
def v2f(va): return va-0x100000+0x80
def word(va): return struct.unpack('<I',D[v2f(va):v2f(va)+4])[0]
# scan backward from va for 'addiu $sp,$sp,-N' = 27bd ffxx  (top bytes 27bd, and imm negative)
va=int(sys.argv[1],16)
a=va
for _ in range(2000):
    a-=4
    w=word(a)
    # addiu sp,sp,imm : opcode 001001 rs=29 rt=29 => 0x27bd
    if (w>>16)==0x27bd and (w&0x8000):
        print('func start candidate %08x  word %08x (frame -0x%x)'%(a,w,(0x10000-(w&0xffff))))
        # only print first found
        break
