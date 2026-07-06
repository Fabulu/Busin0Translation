import sys, zipfile, struct
sys.stdout.reconfigure(encoding='utf-8')
def load(path):
    z=zipfile.ZipFile(path)
    biggest=max(z.namelist(), key=lambda n:z.getinfo(n).file_size)
    return z.read(biggest)
def u32(m,a): return struct.unpack('<I',m[a:a+4])[0]
def u8(m,a): return m[a]
m=load(sys.argv[1])
HEAD=0x578CC4
print(f"=== {sys.argv[1]} ===")
node=u32(m,HEAD)
seen=set(); i=0
while node and node not in seen and i<40:
    seen.add(node); i+=1
    nxt=u32(m,node); prev=u32(m,node+4); fn=u32(m,node+8); ctx=u32(m,node+0xC); flags=u32(m,node+0x10)
    extra=""
    if ctx:
        h1c=u32(m,ctx+0x1c); s70=struct.unpack('<H',m[ctx+0x70:ctx+0x72])[0]
        b8=u8(m,ctx+8)
        extra=f" ctx+1C=0x{h1c:08X} ctx+70(state)=0x{s70:04X} ctx+8=0x{b8:02X}"
    print(f"node 0x{node:08X} next=0x{nxt:08X} fn=0x{fn:08X} ctx=0x{ctx:08X} flags=0x{flags:08X}{extra}")
    node=nxt
