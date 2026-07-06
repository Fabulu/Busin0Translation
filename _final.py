import glob
exe=open('extracted/SLPM_653.78','rb').read()
FOFF=0x80; VBASE=0x100000; FILESZ=0x3fdc80
seg=exe[FOFF:FOFF+FILESZ]
def disk(va,n): o=va-VBASE; return seg[o:o+n]
def dr(p,va,n):
    f=open(p,'rb'); f.seek(va); b=f.read(n); f.close(); return b
p='RAMdumps/19-1_extracted/eeMemory.bin'

# 0x13cae8 region: what is here? show context as ascii
print('=== 0x13cae0 (the d4737275 variant, x8 dumps) ===')
print('DISK ascii:', bytes(c if 32<=c<127 else 46 for c in disk(0x13cad0,64)))
print('DISK hex  :', disk(0x13cae0,16).hex())
print()
# 0x4af400: header 'PsIIlibgraph2500' -> this is sceGsLibgraph global state block
print('=== 0x4af400 block (libgraph) ascii context ===')
print(bytes(c if 32<=c<127 else 46 for c in disk(0x4af400,32)))
print('diff at 0x4af414: DISK',disk(0x4af414,4).hex(),' DUMP',dr(p,0x4af414,4).hex())
print('diff at 0x4af650: DISK',disk(0x4af650,33).hex())
print('               DUMP',dr(p,0x4af650,33).hex())
print('diff at 0x4afd79: DISK',disk(0x4afd79,28).hex())
print('               DUMP',dr(p,0x4afd79,28).hex())
print()
# Is 0x4af4xx CODE or DATA? Check if region looks like MIPS code or zero/data
# Sample a wider window
import struct
print('=== words around 0x4af400..0x4af800 (DISK) ===')
for va in range(0x4af400,0x4af480,4):
    w=struct.unpack('<I',disk(va,4))[0]
    print('  %08x: %08x'%(va,w))
