import sys, struct, zipfile
sys.stdout.reconfigure(encoding='utf-8')
def load(p):
    z=zipfile.ZipFile(p)
    for n in z.namelist():
        if 'eeMemory' in n: return z.read(n)
def w32(m,va): return struct.unpack('<I',m[va:va+4])[0] if 0<=va<=len(m)-4 else None
def walk(m, head_va):
    # head holds pointer to first node
    out=[]
    seen=set()
    node=w32(m,head_va)
    # Some scheduler heads are list-roots, try both: head as node or head as ptr-to-node
    cur=node
    while cur and cur not in seen and 0x80000<cur<0x2000000:
        seen.add(cur)
        nxt=w32(m,cur+0x00)
        fn =w32(m,cur+0x08)
        ctx=w32(m,cur+0x0C)
        out.append((cur,nxt,fn,ctx))
        cur=nxt
        if len(out)>200: break
    return out
for label,p in [('WORKING','tavern104.p2s'),('FROZEN','fuckinghellman.p2s')]:
    m=load('C:/programmieren/wizardrytranslation/ramdumps/'+p)
    print(f'\n===== {label} =====')
    print('head 0x578CC4 ->', hex(w32(m,0x578CC4)))
    lst=walk(m,0x578CC4)
    fns=set()
    for node,nxt,fn,ctx in lst:
        print(f'  node 0x{node:08x} next 0x{nxt:08x} fn 0x{fn:08x} ctx 0x{ctx:08x}')
        fns.add(fn)
    print(f'  ({len(lst)} nodes)')
