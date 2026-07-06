import sys, struct, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,os.path.abspath('tools'))
import sec1_disasm as S
pat=open('build/patched_type2/1197_type02.raw','rb').read()
pri=open('extracted/packdata_raw/1197_type02.raw','rb').read()
okp,ip,s1p,offp=S.walk_resource(pat)
okq,iq,s1q,offq=S.walk_resource(pri)

# Count choice markers 0xFFC0-0xFFCF anywhere in FULL FILE and in sec2.
def countmarkers(b,lo,hi):
    c={}
    for i in range(0,len(b)-1,1):
        w=(b[i]<<8)|b[i+1]
        if 0xFFC0<=w<=0xFFCF:
            c[w]=c.get(w,0)+1
    return c
# aligned scan in sec2 (word stream)
def sec2markers(b,off):
    c={}
    s2=b[off:]
    for i in range(0,len(s2)-1,2):
        w=(s2[i]<<8)|s2[i+1]
        if 0xFFC0<=w<=0xFFCF: c[w]=c.get(w,0)+1
    return c
print("sec2 markers patched:",sorted(sec2markers(pat,offp).items()))
print("sec2 markers pristine:",sorted(sec2markers(pri,offq).items()))

# Section-2 length
print("sec2 len patched=%d pristine=%d"%(len(pat)-offp,len(pri)-offq))

# Check 0x04/0x14 remap targets land within sec2 bounds
import struct
def beu32(b,o):return struct.unpack_from(">I",b,o)[0]
s2len_p=(len(pat)-offp)//2
s2len_q=(len(pri)-offq)//2
bad=[]
for pc,op in sorted(ip.items()):
    if op==0x04:
        off=beu32(s1p,pc+2);cnt=beu32(s1p,pc+6)
        if off+cnt> s2len_p: bad.append(('04',pc,off,cnt,s2len_p))
    elif op==0x14:
        off=beu32(s1p,pc+6);cnt=beu32(s1p,pc+10)
        if off+cnt> s2len_p: bad.append(('14',pc,off,cnt,s2len_p))
print("patched out-of-bounds sec2 refs:",len(bad))
for x in bad[:20]:print("  ",x)
