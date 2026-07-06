import struct,sys,os
sys.stdout.reconfigure(encoding='utf-8')
v99=open('build/patched_type2/1197_type02.raw','rb').read()
pri=open('extracted/packdata_raw/1197_type02.raw','rb').read()
def parts(d):
    o=struct.unpack_from("<I",d,0x18)[0]; return d[0x20:o], d[o:], o
v1,vs2,vo=parts(v99); p1,ps2,po=parts(pri)
# sec2 begins with an offset table? Many type-02 sec2 start with a u32 count + offsets.
# Let's inspect first words of sec2.
print("v99 sec2 head:",vs2[:32].hex())
print("pri sec2 head:",ps2[:32].hex())
# Find context of 0xFFD2 in pristine - print 8 words around first few
def find_all(s2,w):
    r=[]
    for i in range(0,len(s2)-1,2):
        if (s2[i]<<8|s2[i+1])==w: r.append(i)
    return r
locs=find_all(ps2,0xFFD2)
print("\npristine 0xFFD2 first 6 contexts (word idx, surrounding words):")
for off in locs[:6]:
    wi=off//2
    ctx=[ (ps2[off-6+k] if 0<=off-6+k<len(ps2) else 0) for k in range(0,16)]
    words=[ "%04x"%((ps2[max(0,off-6)+j]<<8|ps2[max(0,off-6)+j+1])) for j in range(0,16,2)]
    print("  wordidx %d: ..%s.."%(wi," ".join(words)))
# v99 single 0xFFD2
vlocs=find_all(vs2,0xFFD2)
print("\nv99 0xFFD2 locations (word idx):",[x//2 for x in vlocs])
