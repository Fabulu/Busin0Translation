import sys,struct
EXE=r"C:\programmieren\wizardrytranslation\extracted\SLPM_653.78"
VA_BASE=0xFFF80
exe=open(EXE,'rb').read()
target=int(sys.argv[1],16)
# scan for jal/j to target, and for the target appearing as a data word (table pointer)
jal_word_op3 = ((target>>2)&0x03FFFFFF)
n=len(exe)//4
for i in range(n):
    w=struct.unpack('<I',exe[i*4:i*4+4])[0]
    va=VA_BASE+i*4
    op=(w>>26)&0x3F
    if op in (2,3):
        tgt=((w&0x03FFFFFF)<<2)|(va&0xF0000000)
        if tgt==target:
            print(f"{va:08X}  {'jal' if op==3 else 'j'} 0x{target:X}")
    # data word pointer (full VA)
    if w==target:
        print(f"{va:08X}  .word 0x{w:08X}  <-- table/data ptr")
