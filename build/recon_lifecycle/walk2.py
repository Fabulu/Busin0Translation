import struct, zipfile, sys
sys.stdout.reconfigure(encoding='utf-8')
def load(p):
    z=zipfile.ZipFile(p)
    for n in z.namelist():
        if 'eeMemory' in n: return z.read(n)
def w32(m,va): return struct.unpack('<I',m[va:va+4])[0] if 0<=va<=len(m)-4 else 0
# node layout (confirmed): +0 next, +4 prev?, +8 fn, +0xC ctx  (16B walkable via next)
for lbl,p in [('WORKING','tavern104.p2s'),('FROZEN','fuckinghellman.p2s')]:
    m=load('C:/programmieren/wizardrytranslation/ramdumps/'+p)
    head=w32(m,0x578CC4)
    print(f'\n===== {lbl} ===== head=0x{head:08x} curScreen=0x{w32(m,0x504FF0-25136):08x}')
    cur=head; seen=set(); i=0
    while cur and cur not in seen and 0x500000<cur<0x600000 and i<40:
        seen.add(cur); i+=1
        nxt=w32(m,cur+0); p4=w32(m,cur+4); fn=w32(m,cur+8); ctx=w32(m,cur+0xC)
        tag=''
        if fn==0x2f2490: tag=' <== HUB 0x2F2490'
        if fn==0x3a2440: tag=' <-- 0x3A2440'
        if fn==0x3a25f0: tag=' (mgr 0x3A25F0)'
        print(f'  0x{cur:08x}: next=0x{nxt:08x} +4=0x{p4:08x} fn=0x{fn:08x} ctx=0x{ctx:08x}{tag}')
        cur=nxt
