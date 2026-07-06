import sys, zipfile, struct
sys.stdout.reconfigure(encoding='utf-8')
def load(p):
    z=zipfile.ZipFile(p)
    for n in z.namelist():
        if 'eeMemory' in n: return z.read(n)
def u32(m,va): return struct.unpack('<I',m[va:va+4])[0]
work=load(r'C:\programmieren\wizardrytranslation\ramdumps\tavern104.p2s')
froz=load(r'C:\programmieren\wizardrytranslation\ramdumps\fuckinghellman.p2s')
gp=0x504FF0
for tag,p in [('work',work),('froz',froz)]:
    edgep=u32(p,gp-0x6438)   # 0x4FEBB8 -> 0x56D520
    e1c=u32(p,edgep+0x1c)
    ctx=u32(p,u32(p,0x4FEDC0)+0x0C)
    c290=u32(p,ctx+0x290)
    print(f"{tag}: edge_struct=0x{edgep:08X} edge+0x1C=0x{e1c:08X}  ctx+0x290=0x{c290:X} (bits2|3={c290&0xC:X})")
