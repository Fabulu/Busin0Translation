import sys, struct, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools')
from patch_section1_offsets import walk, extract_records, _bucket_labels, HEADER_SIZE
RAW='extracted/packdata_raw'
def lbl(res):
    raw=open(f'{RAW}/{res:04d}_type02.raw','rb').read()
    s2s=struct.unpack_from('<I',raw,0x14)[0];s2o=struct.unpack_from('<I',raw,0x18)[0]
    sec1=raw[HEADER_SIZE:s2o];ok,instrs=walk(sec1);recs=extract_records(sec1,instrs)
    sec2=raw[s2o:s2o+s2s];n=len(sec2)//2
    words=[struct.unpack_from('>H',sec2,i*2)[0] for i in range(n)]
    grps=[];start=0
    for i in range(n):
        if words[i]==0xFFFF: grps.append(words[start:i]);start=i+1
    ranges=[];p=0
    for gg in grps:
        ranges.append((p,p+len(gg)));p+=len(gg)+1
    pg,_=_bucket_labels(recs['label'],ranges,p)
    return set(pg.keys())
# complained dialogue groups
for res,gis in [(1196,[575,577,578,583,602,653,654,659]),(1197,[925])]:
    wl=lbl(res)
    for gi in gis:
        print(f"R{res} g{gi}: has 0x14 name-island = {gi in wl}")
