import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open(r"C:/programmieren/wizardrytranslation/build/recon_tri/extract/requestbroken__ee.bin","rb").read()
def u32(a): return struct.unpack_from("<I",ee,a)[0]
# A scene-manager/script ctx: per the caller code, +0x290 (656) flags, +0x29C (668) u16 counter, +0 pc.
# Find structs where +0x290 has one of the blocked bits (0x10/0x20/0x40/0x80) set AND +0 looks like a heap ptr (0x0100xxxx..0x02000000)
print("structs with blocked-flag bits set at +0x290 and a heap-ptr at +0:")
cnt=0
for a in range(0x00100000,0x01F00000,4):
    flags=u32(a+0x290) if a+0x294<len(ee) else 0
    if flags & 0xF0 and (flags>>8)==0:  # only low byte flags, blocked bits
        pc=u32(a)
        if 0x01000000<=pc<0x02000000:
            counter=struct.unpack_from("<H",ee,a+0x29c)[0]
            print("  ctx@%08X pc=%08X flags=%02X cnt=%d"%(a,pc,flags&0xff,counter))
            cnt+=1
            if cnt>30: break
