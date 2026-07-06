import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open('build/recon_portrait4/extract/request__ee.bin','rb').read()
# Find the ACTIVE party slots (the bar shows leader 'A A' + Vera). Active party usually a small fixed table.
# Search for ascii 'A' name-value = 'A' gid? english_glyph_table: A->? ascii name_val= gid+95. 'A' likely cap.
# In R1892 codec ascii cap A = 128 (from earlier: Aurora started 128). So 'A'=128 LE.
def le(words): return b''.join(struct.pack('<H',w) for w in words)
# 'A A' = 128,(space?),128 ? space glyph 0? Look for 128 runs
import re
A=le([128])
# scan for standalone 'A' patterns: 128 then 0000 then 128
pat=le([128,0,128])
i=ee.find(pat);hits=[]
while i!=-1 and len(hits)<20:
    hits.append(i);i=ee.find(pat,i+1)
print("'A?A' (128,0,128) hits:",['0x%X'%x for x in hits])
# 'A A' with space glyph maybe 0x20-0x20+95=95? space ascii=0x20 gid: name_val=0+95? Actually ' '=gid for space
# Try 128 FFFF 128 won't. Try just two 128 adjacent
for pat,nm in [(le([128,128]),'128,128'),(le([128]),'single 128')]:
    i=ee.find(pat);hits=[]
    while i!=-1 and len(hits)<30:
        hits.append(i);i=ee.find(pat,i+1)
    print(nm,'->',len(hits),'hits',['0x%X'%x for x in hits[:12]])
