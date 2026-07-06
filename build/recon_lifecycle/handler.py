import struct, zipfile, sys
sys.stdout.reconfigure(encoding='utf-8')
def load(p):
    z=zipfile.ZipFile(p)
    for n in z.namelist():
        if 'eeMemory' in n: return z.read(n)
def w32(m,va): return struct.unpack('<I',m[va:va+4])[0]
GP=0x504FF0
for lbl,p in [('WORKING','tavern104.p2s'),('FROZEN','fuckinghellman.p2s')]:
    m=load('C:/programmieren/wizardrytranslation/ramdumps/'+p)
    h_node=w32(m,GP-25136)  # 0x4FE9C0 current screen handler node
    print(f'--- {lbl} ---  [0x4FE9C0]=node 0x{h_node:08x}')
    if 0x80000<h_node<0x2000000:
        nxt=w32(m,h_node+0); f04=w32(m,h_node+4); fn=w32(m,h_node+8); ctx=w32(m,h_node+0xC)
        print(f'   node: next=0x{nxt:08x} +4=0x{f04:08x} fn=0x{fn:08x} ctx=0x{ctx:08x}')
    # other handler-related gp ptrs
    for off,nm in [(-25144,'0x4FE9B8'),(-25140,'0x4FE9BC'),(-25132,'0x4FE9C4'),(-25128,'0x4FE9C8')]:
        print(f'   gp{off} {nm} = 0x{w32(m,GP+off):08x}')
