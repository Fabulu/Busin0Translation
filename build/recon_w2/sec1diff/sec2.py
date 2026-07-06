import struct,sys,os
sys.stdout.reconfigure(encoding='utf-8')
v99=open('build/patched_type2/1197_type02.raw','rb').read()
pri=open('extracted/packdata_raw/1197_type02.raw','rb').read()
def sec2(d): 
    o=struct.unpack_from("<I",d,0x18)[0]; return d[o:],o
vs2,vo=sec2(v99); ps2,po=sec2(pri)
print("v99 sec2_off=0x%x len=%d (words=%d)"%(vo,len(vs2),len(vs2)//2))
print("pri sec2_off=0x%x len=%d (words=%d)"%(po,len(ps2),len(ps2)//2))
# sec2 is a glyph word stream. The 0x04 DISPLAY uses word offset+count.
# Around the runaway: DISPLAY at 0x9da9 off=44679 cnt=77 (v96 remap). For v99 the off differs.
# Let's just dump the LAST display group in v99 and pristine sec2 (the Gin convo tail) by reading
# words. But offsets differ. Instead, scan for 0xFFFE (group terminator?) and 0xFFFF counts.
def wcount(s2,w):
    c=0
    for i in range(0,len(s2)-1,2):
        if (s2[i]<<8|s2[i+1])==w: c+=1
    return c
for w in [0xFFFF,0xFFFE,0xFFFD,0xFFC0,0xFFC1,0xFFD2]:
    print("word 0x%04x: v99=%d pri=%d"%(w,wcount(vs2,w),wcount(ps2,w)))
