import os,glob
exe=open('extracted/SLPM_653.78','rb').read()
FOFF=0x80; VBASE=0x100000; FILESZ=0x3fdc80
seg=exe[FOFF:FOFF+FILESZ]
VEND=VBASE+FILESZ

def disk(va,n): o=va-VBASE; return seg[o:o+n]
def dumpread(p,va,n):
    f=open(p,'rb'); f.seek(va); b=f.read(n); f.close(); return b

# pick representative dumps
ex_aheavy='RAMdumps/_b6_aheavyfog/eeMemory.bin'
ex_19='RAMdumps/19-1_extracted/eeMemory.bin'
ex_batt='RAMdumps/_battlecameraspin/eeMemory.bin'
import glob as g
def find(name):
    for p in g.glob('RAMdumps/**/eeMemory.bin',recursive=True):
        if name in p: return p
    return None
ex_aheavy=find('aheavyfog') or ex_aheavy
ex_19=find('19-1') 
ex_batt=find('battlecameraspin')

def hx(b): return b.hex()

# 0x4af400 region - present in ALL 73, matchesDisk=0
print('=== 0x4af400 (ALL 73 dumps differ, single variant) ===')
print('DISK :',hx(disk(0x4af400,48)))
print('DUMP :',hx(dumpread(ex_19,0x4af400,48)))
print()
print('=== 0x4af600 ===')
print('DISK :',hx(disk(0x4af600,48)))
print('DUMP :',hx(dumpread(ex_19,0x4af600,48)))
print()
# 0x2f2500 region (59 dumps share variant 4bcc18fb)
print('=== 0x2f2500 (interpreter area) ===')
print('DISK :',hx(disk(0x2f2500,48)))
print('DUMP :',hx(dumpread(ex_aheavy,0x2f2500,48)))
print()
# 0x463a00 / 0x463e00  (59 dumps)
print('=== 0x463a00 ===')
print('DISK :',hx(disk(0x463a00,48)))
print('DUMP :',hx(dumpread(ex_aheavy,0x463a00,48)))
print('=== 0x463e00 ===')
print('DISK :',hx(disk(0x463e00,48)))
print('DUMP :',hx(dumpread(ex_aheavy,0x463e00,48)))
