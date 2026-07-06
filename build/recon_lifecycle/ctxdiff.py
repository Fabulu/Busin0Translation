import struct, zipfile, sys
sys.stdout.reconfigure(encoding='utf-8')
def load(p):
    z=zipfile.ZipFile(p)
    for n in z.namelist():
        if 'eeMemory' in n: return z.read(n)
W=load('C:/programmieren/wizardrytranslation/ramdumps/tavern104.p2s')
F=load('C:/programmieren/wizardrytranslation/ramdumps/fuckinghellman.p2s')
CTX=0x01137a00
# diff a wider range
N=0x800
print(f'VM ctx 0x{CTX:08x} diffs over 0x{N:x} bytes (offset: working -> frozen):')
i=0
while i<N:
    if W[CTX+i]!=F[CTX+i]:
        # group consecutive
        j=i
        while j<N and W[CTX+j]!=F[CTX+j]: j+=1
        wv=W[CTX+i:CTX+j].hex(); fv=F[CTX+i:CTX+j].hex()
        # also as u32 if aligned & 4 wide
        extra=''
        if (i%4)==0 and (j-i)>=4:
            wu=struct.unpack('<I',W[CTX+i:CTX+i+4])[0]; fu=struct.unpack('<I',F[CTX+i:CTX+i+4])[0]
            extra=f'  u32: 0x{wu:08x} -> 0x{fu:08x}'
        print(f'  +0x{i:03x} ({i:4}): {wv} -> {fv}{extra}')
        i=j
    else:
        i+=1
