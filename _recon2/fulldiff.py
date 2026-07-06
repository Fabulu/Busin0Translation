import sys, zipfile, struct
sys.stdout.reconfigure(encoding='utf-8')
def load(p):
    z=zipfile.ZipFile(p)
    for n in z.namelist():
        if 'eeMemory' in n: return z.read(n)
work=load(r'C:\programmieren\wizardrytranslation\ramdumps\tavern104.p2s')
froz=load(r'C:\programmieren\wizardrytranslation\ramdumps\fuckinghellman.p2s')

# diff ctx object 0x1137A00 .. +0x300
def diffrange(base,size,label):
    print(f"--- {label} 0x{base:08X}..+0x{size:X} ---")
    o=0
    while o<size:
        if work[base+o]!=froz[base+o]:
            # show 4-byte aligned word
            wa=base+(o&~3)
            w=struct.unpack('<I',work[wa:wa+4])[0]
            f=struct.unpack('<I',froz[wa:wa+4])[0]
            print(f"  +0x{(wa-base):03X} (0x{wa:08X}): work=0x{w:08X} froz=0x{f:08X}")
            o=(o&~3)+4
        else:
            o+=1
diffrange(0x1137A00,0x300,'hub ctx')
# input/menu globals region around gp-0x6xxx and gp-0x7xxx
print()
diffrange(0x4FE600,0x200,'input globals 0x4FE600')
print()
diffrange(0x4FD200,0x200,'input-lock region 0x4FD200')
