import sys,struct
EXE=r"C:\programmieren\wizardrytranslation\extracted\SLPM_653.78"
exe=open(EXE,'rb').read()
def fo(va): return va-0x100000+0x80
va=int(sys.argv[1],16)
# walk backward to find 'addiu sp,sp,-N' (function prologue)
v=va
while v>va-0x4000:
    w=struct.unpack_from('<I',exe,fo(v))[0]
    if (w>>16)==0x27BD and (w&0x8000):  # addiu sp,sp,neg
        print("PROLOGUE %08X: %08X"%(v,w)); break
    v-=4
