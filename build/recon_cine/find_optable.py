import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
exe=open("extracted/SLPM_653.78","rb").read()
# search for 0x002F92B0 as a 4-byte LE value (handler pointer in a table)
needle=struct.pack("<I",0x002F92B0)
i=0; hits=[]
while True:
    j=exe.find(needle,i)
    if j<0: break
    hits.append(0x100000+j-0x80); i=j+1
print("0x2F92B0 as data (handler table entry) at VA:", [f"0x{v:08X}" for v in hits])
# also neighbors 0x2F92F0 (page register opcode), 0x2F9320
for n in (0x2F92F0,0x2F9320,0x2F9270):
    nd=struct.pack("<I",n); i=0
    while True:
        j=exe.find(nd,i)
        if j<0: break
        print(f"  0x{n:08X} as data at VA 0x{0x100000+j-0x80:08X}"); i=j+1
