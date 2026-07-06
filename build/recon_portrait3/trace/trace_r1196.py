import sys, struct, json, glob, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'tools')
sys.path.insert(0, 'build')
import patch_section1_offsets as P

RAW='extracted/packdata_raw/1196_type02.raw'
raw=open(RAW,'rb').read()
sec2_size=struct.unpack_from('<I',raw,0x14)[0]
sec2_off=struct.unpack_from('<I',raw,0x18)[0]
print("sec2_off",hex(sec2_off),"sec2_size",sec2_size,"file",len(raw))
sec2=raw[sec2_off:sec2_off+sec2_size]
groups,trail=P.parse_sec2_group_offsets(sec2)
print("n groups",len(groups),"trailing_start",trail)

def words(gi):
    gs,ge=groups[gi]
    return [struct.unpack_from('>H',sec2,(gs+k)*2)[0] for k in range(ge-gs)]

# msg_index 577 -> group index 577 (FFFF group). Show it.
for mi in [577]:
    w=words(mi)
    print(f"\n=== ORIGINAL group {mi} ({len(w)} words) ===")
    print(' '.join('%04X'%x for x in w))
    # decode JP attempt
    jp=P._decode_jp(w)
    print("decode_jp ->", jp)
