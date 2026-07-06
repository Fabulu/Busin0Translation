import struct, zipfile, sys
sys.stdout.reconfigure(encoding='utf-8')
def load(p):
    z=zipfile.ZipFile(p)
    for n in z.namelist():
        if 'eeMemory' in n: return z.read(n)
def by(m,va): return m[va]
def w32(m,va): return struct.unpack('<I',m[va:va+4])[0]
GP=0x504FF0
for lbl,p in [('WORKING','tavern104.p2s'),('FROZEN','fuckinghellman.p2s')]:
    m=load('C:/programmieren/wizardrytranslation/ramdumps/'+p)
    print(f'--- {lbl} ---')
    print(f'  0x4FE918 (win-state bitfield) = 0x{by(m,0x4FE918):02x}  bit0={by(m,0x4FE918)&1} bit2={(by(m,0x4FE918)>>2)&1} bit7={(by(m,0x4FE918)>>7)&1}')
    print(f'  0x4FE914 (gp-26396)           = 0x{by(m,0x4FE914):02x}')
    print(f'  0x4FE910 (gp-26400)           = 0x{by(m,0x4FE910):02x}')
    # the manager s1 ctx (0x3A25F0 node ctx 0x010a4280) field 18, field0
    ctx=0x010a4280
    print(f'  mgr ctx0x{ctx:08x}+18 = {by(m,ctx+18)}  +0(0)=0x{w32(m,ctx):08x}')
    print(f'  gp-26332 (0x4FE964 active-win ptr) = 0x{w32(m,GP-26332):08x}')
