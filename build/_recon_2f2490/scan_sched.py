import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open(sys.argv[1],'rb').read()
def u32(a): return struct.unpack('<I',ee[a:a+4])[0]
def u16(a): return struct.unpack('<H',ee[a:a+2])[0]
# scheduler head ptr at 0x578CC4, menu-obj ptr global [0x4FEDC0]
head=u32(0x578CC4)
print(f"sched head ptr [0x578CC4] = 0x{head:08X}")
print(f"menu-obj global [0x4FEDC0] = 0x{u32(0x4FEDC0):08X}")
print(f"hub script base [0x564ED0] = 0x{u32(0x564ED0):08X}  [0x564ED4]=0x{u32(0x564ED4):08X}")
print()
# walk scheduler linked list. node: +0 next, +4 prev, +8 fn, +C ctx, +10 flags
print("=== scheduler walk ===")
node=head
seen=set()
i=0
while node and node not in seen and i<60:
    seen.add(node)
    nxt=u32(node+0); prv=u32(node+4); fn=u32(node+8); ctx=u32(node+0xC); fl=u32(node+0x10)
    cursor=u32(ctx) if ctx and ctx<0x2000000 else 0
    print(f"[{i}] node=0x{node:08X} next=0x{nxt:08X} prev=0x{prv:08X} fn=0x{fn:08X} ctx=0x{ctx:08X} flags=0x{fl:08X} cursor=0x{cursor:08X}")
    node=nxt
    i+=1
