import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
EXE=r"C:\programmieren\wizardrytranslation\extracted\SLPM_653.78"
VA_BASE=0xFFF80
exe=open(EXE,'rb').read()
target=int(sys.argv[1],16)
# jal target encoding: op=3, addr=(target>>2)&0x03FFFFFF
jal_word = (0x03<<26) | ((target>>2)&0x03FFFFFF)
j_word   = (0x02<<26) | ((target>>2)&0x03FFFFFF)
print(f"searching for jal/j 0x{target:X}  (jal={jal_word:08X} j={j_word:08X})")
n=len(exe)
for fo in range(0, n-3, 4):
    w=struct.unpack('<I',exe[fo:fo+4])[0]
    if w==jal_word:
        va=fo+VA_BASE
        print(f"  JAL @ VA {va:08X} (fo {fo:06X})")
    elif w==j_word:
        va=fo+VA_BASE
        print(f"  J   @ VA {va:08X} (fo {fo:06X})")
