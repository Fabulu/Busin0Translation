import sys, struct, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools')
from patch_section1_offsets import walk, extract_records, parse_sec2_group_offsets, _bucket_labels, HEADER_SIZE
RAW='extracted/packdata_raw'
def analyze(res):
    raw=open(f'{RAW}/{res:04d}_type02.raw','rb').read()
    sec2_size=struct.unpack_from('<I',raw,0x14)[0]
    sec2_off=struct.unpack_from('<I',raw,0x18)[0]
    sec1=raw[HEADER_SIZE:sec2_off]
    ok,instrs=walk(sec1)
    if not ok: 
        print(f"R{res}: sec1 walk failed"); return
    recs=extract_records(sec1,instrs)
    sec2=raw[sec2_off:sec2_off+sec2_size]
    n=len(sec2)//2
    words=[struct.unpack_from('>H',sec2,i*2)[0] for i in range(n)]
    grps=[];start=0;ranges=[];pos=0
    for i in range(n):
        if words[i]==0xFFFF:
            grps.append(words[start:i]);start=i+1
    p=0
    for gg in grps:
        ranges.append((p,p+len(gg)));p+=len(gg)+1
    trail=p
    per_group,_=_bucket_labels(recs['label'],ranges,trail)
    # groups WITH a 0x14 label slice = dialogue (speaker box); without = narration
    with_label=set(per_group.keys())
    print(f"R{res}: {len(grps)} groups, {len(with_label)} have 0x14 name-island")
    for gi in [569,575,577]:
        if gi<len(grps):
            print(f"   g{gi}: has 0x14 label = {gi in with_label}  slices={per_group.get(gi)}")
analyze(1196)
analyze(1197)
