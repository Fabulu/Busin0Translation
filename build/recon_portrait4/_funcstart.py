import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
EXE=open('extracted/SLPM_653.78','rb').read()
def v2f(va): return va-0x100000+0x80
# scan backward from va for 'addiu $sp,$sp,-N' (op=0x09, rs=rt=29) preceded by enough
va=int(sys.argv[1],16) if len(sys.argv)>1 else 0x302C00
fo=v2f(va)
for f in range(fo, fo-0x2000, -4):
    w=struct.unpack_from('<I',EXE,f)[0]
    op=(w>>26)&0x3F; rs=(w>>21)&0x1F; rt=(w>>16)&0x1F; imm=w&0xFFFF
    if op==0x09 and rs==29 and rt==29 and imm>=0x8000:  # addiu sp,sp,-N
        print(f"prologue at va=0x{f-0x80+0x100000:08X} word=0x{w:08X} (sub sp {0x10000-imm})")
        break
