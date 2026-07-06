import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
EXE=r"C:\programmieren\wizardrytranslation\extracted\SLPM_653.78"
VA_BASE=0xFFF80
exe=open(EXE,'rb').read()
va=int(sys.argv[1],16)
fo=va-VA_BASE
# walk back to find addiu $sp,$sp,-N (prologue) preceded by jr/j (prev fn end)
cur=fo
while cur>0:
    w=struct.unpack('<I',exe[cur:cur+4])[0]
    op=(w>>26)&0x3F; rs=(w>>21)&0x1F; rt=(w>>16)&0x1F; imm=w&0xFFFF
    s=imm-0x10000 if imm&0x8000 else imm
    if op==0x09 and rs==29 and rt==29 and s<0:  # addiu sp,sp,-N
        print(f"prologue @ VA {cur+VA_BASE:08X} (fo {cur:06X})  sp-={-s:#x}")
        break
    cur-=4
