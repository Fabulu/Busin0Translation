import sys, struct, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools')
from patch_section1_offsets import walk, extract_records, HEADER_SIZE
RAW='extracted/packdata_raw'
raw=open(f'{RAW}/1196_type02.raw','rb').read()
s2s=struct.unpack_from('<I',raw,0x14)[0];s2o=struct.unpack_from('<I',raw,0x18)[0]
sec1=raw[HEADER_SIZE:s2o]
ok,instrs=walk(sec1);recs=extract_records(sec1,instrs)
sec2=raw[s2o:s2o+s2s];n=len(sec2)//2
words=[struct.unpack_from('>H',sec2,i*2)[0] for i in range(n)]
grps=[];start=0
for i in range(n):
    if words[i]==0xFFFF: grps.append(words[start:i]);start=i+1
goff=[];p=0
for gg in grps:
    goff.append(p);p+=len(gg)+1
# All display records sorted; find which cover groups 569-583
disp=sorted(recs['display'],key=lambda d:d['off'])
print("display records covering word offsets 18400-19200:")
for d in disp:
    if 18400<=d['off']<=19200:
        # which groups does off..off+cnt span?
        gs=[gi for gi,o in enumerate(goff) if d['off']<=o<d['off']+d['cnt']]
        print(f"  pc=0x{d['pc']:X} off={d['off']} cnt={d['cnt']} -> spans groups {gs}")
