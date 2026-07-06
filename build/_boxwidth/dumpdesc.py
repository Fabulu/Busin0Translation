import sys,zipfile,struct
sys.stdout.reconfigure(encoding='utf-8')
p=sys.argv[1]
z=zipfile.ZipFile(p)
ee=None
for n in z.namelist():
    if n.endswith('eeMemory.bin'): ee=z.read(n)
print(p, "ee len", len(ee))
PTR=0x565150
def rd(va,n): return ee[va:va+n]
def s16(va):
    v=struct.unpack('<h',ee[va:va+2])[0]; return v
def u16(va): return struct.unpack('<H',ee[va:va+2])[0]
def s32(va): return struct.unpack('<i',ee[va:va+4])[0]
for i in range(32):
    pp=s32(PTR+i*4)&0xffffffff
    if pp==0 or pp>0x2000000: continue
    bw=s16(pp+0x1c); bx=s16(pp+0x3c); be=s16(pp+0x3e)
    f38=s16(pp+0x38); f40=s16(pp+0x40)
    print(f"[{i:2}] desc=0x{pp:07X} +1c(bw)={bw:5} +3c(boxX)={bx:6} +3e={be:6} +38={f38:6} +40={f40:6}")
