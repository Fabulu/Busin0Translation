import sys,struct,zipfile
sys.stdout.reconfigure(encoding='utf-8')
def load(p):
    z=zipfile.ZipFile(p)
    for n in z.namelist():
        if 'eeMemory' in n or n.endswith('.bin'): return z.read(n)
    return z.read(z.namelist()[0])
work=load(r"RAMdumps/tavern104.p2s"); froz=load(r"RAMdumps/fuckinghellman.p2s")
ctx=0x1137a00
print("Diffs in ctx 0x1137a00 .. +0x400:")
for off in range(0,0x400,4):
    a=ctx+off
    wv=struct.unpack('<I',work[a:a+4])[0]
    fv=struct.unpack('<I',froz[a:a+4])[0]
    if wv!=fv:
        print(f"  +{off:03X}  work={wv:#010x}  froz={fv:#010x}")
