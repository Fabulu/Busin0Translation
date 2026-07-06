import sys, struct, os, json, glob
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools')
from patch_section1_offsets import walk, extract_records, _bucket_labels, HEADER_SIZE
RAW='extracted/packdata_raw'

# Load English translations to see what non-labeled groups actually say
all_trans={}
for fn in sorted(glob.glob('data/type2_translated/batch_*.json')):
    try:
        for e in json.load(open(fn,encoding='utf-8')):
            all_trans.setdefault(e['resource'],{})[e['msg_index']]=e.get('english','')
    except: pass

def labels_for(res):
    raw=open(f'{RAW}/{res:04d}_type02.raw','rb').read()
    sec2_size=struct.unpack_from('<I',raw,0x14)[0]
    sec2_off=struct.unpack_from('<I',raw,0x18)[0]
    sec1=raw[HEADER_SIZE:sec2_off]
    ok,instrs=walk(sec1)
    if not ok: return None,None
    recs=extract_records(sec1,instrs)
    sec2=raw[sec2_off:sec2_off+sec2_size]
    n=len(sec2)//2
    words=[struct.unpack_from('>H',sec2,i*2)[0] for i in range(n)]
    grps=[];start=0
    for i in range(n):
        if words[i]==0xFFFF: grps.append(words[start:i]);start=i+1
    ranges=[];p=0
    for gg in grps:
        ranges.append((p,p+len(gg)));p+=len(gg)+1
    per_group,_=_bucket_labels(recs['label'],ranges,p)
    return set(per_group.keys()),grps

for res in [1196]:
    wl,grps=labels_for(res)
    tr=all_trans.get(res,{})
    # Show some translated groups that have NO label (would be 'narration' width)
    print(f"R{res}: translated groups without 0x14 label (narration-width candidates):")
    cnt=0
    for mi in sorted(tr):
        if mi not in wl and tr[mi] and not any(ord(c)>127 for c in tr[mi]):
            print(f"  g{mi} (NO label): {tr[mi][:70]!r}")
            cnt+=1
            if cnt>=15: break
    print(f"\nR{res}: translated groups WITH 0x14 label (dialogue-width):")
    cnt=0
    for mi in sorted(tr):
        if mi in wl and tr[mi] and not any(ord(c)>127 for c in tr[mi]):
            print(f"  g{mi} (label): {tr[mi][:70]!r}")
            cnt+=1
            if cnt>=15: break
