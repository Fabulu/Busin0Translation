import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools')
from sec1_disasm import walk, extract_records
HEADER=0x20
p='build/packdata_resources/1196_type02.raw'
d=open(p,'rb').read()
sec2_off=struct.unpack_from('<I',d,0x18)[0]
sec2_size=struct.unpack_from('<I',d,0x14)[0]
nwords=sec2_size//2
words=struct.unpack_from('>%dH'%nwords,d,sec2_off)
# narration glyph stream offset in file = 0x101A8; word index:
woff=(0x101A8 - sec2_off)//2
print('sec2_off=0x%X narration file off=0x101A8 -> word idx=%d'%(sec2_off,woff))
# show the FFFF group boundaries around it
# find the FFFF group start containing woff
start=0
for i in range(woff,-1,-1):
    if words[i]==0xFFFF:
        start=i+1; break
print('group start word idx=%d (FFFF at %d)'%(start,start-1))
sec1=d[HEADER:sec2_off]
ok,instrs=walk(sec1)
print('walk ok=%s ninstr=%d'%(ok,len(instrs)))
recs=extract_records(sec1,instrs)
for kind in recs:
    for r in recs[kind]:
        off=r.get('off'); cnt=r.get('cnt')
        if off is not None and off<=start<off+(cnt or 0) or (off==start) or (off is not None and start-3<=off<=start+1):
            print(f"  {kind}: pc=0x{r['pc']:X} off={off} cnt={cnt} param={r.get('param')}")
# Also list ALL records referencing near woff
print('--- records with off within [%d,%d] ---'%(start-2,woff+5))
for kind in recs:
    for r in recs[kind]:
        off=r.get('off')
        if off is not None and start-2<=off<=woff+5:
            print(f"  {kind}: pc=0x{r['pc']:X} op-rec off={off} cnt={r.get('cnt')} param={r.get('param')}")
