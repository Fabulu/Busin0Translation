import sys,struct,zipfile
sys.stdout.reconfigure(encoding='utf-8')
def load(p):
    z=zipfile.ZipFile(p)
    for n in z.namelist():
        if 'eeMemory' in n or n.endswith('.bin'):
            return z.read(n)
    return z.read(z.namelist()[0])
work=load(r"RAMdumps/tavern104.p2s")
froz=load(r"RAMdumps/fuckinghellman.p2s")
print("work len",len(work),"froz len",len(froz))
def u8(m,a): return m[a]
def u16(m,a): return struct.unpack('<H',m[a:a+2])[0]
def u32(m,a): return struct.unpack('<I',m[a:a+4])[0]
gp=0x504FF0
labels={
 '[gp-0x7334] early-exit gate (0x131D20)':(gp-0x7334,'u8'),
 '[gp-0x694C] INPUT edges word (0x2F15C0)':(gp-0x694C,'u32'),
 '[gp-0x6944] gate A (0x2F1590)':(gp-0x6944,'u8'),
 '[gp-0x6964] gate B (0x2F15A0)':(gp-0x6964,'u8'),
 '[gp-0x693C] busy byte (0x200 blk)':(gp-0x693C,'u8'),
 '[gp-0x6230] menu obj ptr':(gp-0x6230,'u32'),
 '[gp-0x62D8] (sub2240 reads)':(gp-0x62D8,'u8'),
 '[gp-0x68C8] 30B210 sel state':(gp-0x68C8,'u16'),
 '[gp-0x68D4] 30C920 sel state':(gp-0x68D4,'u16'),
 '[0x57473B] 495E00 mode byte':(0x57473B,'u8'),
 '[0x3A2B52] lhu 0x200blk (0x3a*0x10000-0x14ae)':(0x3A0000-0x14ae+0x20000,'u16'),
}
# fix the 0x3a one: lui at,0x3a -> at=0x3A0000 ; lhu v0,-0x14ae(at) -> 0x3A0000-0x14ae=0x39EB52
labels['[0x39EB52] 0x200blk lhu']=(0x39EB52,'u16')
del labels['[0x3A2B52] lhu 0x200blk (0x3a*0x10000-0x14ae)']
def rd(m,a,t):
    return {'u8':u8,'u16':u16,'u32':u32}[t](m,a)
for lbl,(a,t) in labels.items():
    wv=rd(work,a,t); fv=rd(froz,a,t)
    mark=' <==DIFF' if wv!=fv else ''
    print(f"{a:08X} {t:4} {lbl:48} work={wv:#x}  froz={fv:#x}{mark}")
