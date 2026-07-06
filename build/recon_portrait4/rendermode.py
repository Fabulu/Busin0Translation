import sys, struct, os, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools')
from patch_section1_offsets import walk, extract_records, HEADER_SIZE
RAW='extracted/packdata_raw'
raw=open(f'{RAW}/1196_type02.raw','rb').read()
sec2_size=struct.unpack_from('<I',raw,0x14)[0]
sec2_off=struct.unpack_from('<I',raw,0x18)[0]
sec1=raw[HEADER_SIZE:sec2_off]
ok,instrs=walk(sec1)
recs=extract_records(sec1,instrs)
# What record types reference group offsets? The text-draw opcode that picks
# centered-vs-left must carry the group. Let's see all record keys.
print("record keys:",list(recs.keys()))
for k in recs:
    print(f"  {k}: {len(recs[k])} records; sample:",recs[k][:3])
