import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools')
from patch_section1_offsets import walk, extract_records, HEADER_SIZE
RAW='extracted/packdata_raw'
raw=open(f'{RAW}/1196_type02.raw','rb').read()
s2o=struct.unpack_from('<I',raw,0x18)[0]
sec1=raw[HEADER_SIZE:s2o]
# print raw bytes at each display pc; the 0x04 opcode format: 04 ?? off(u32) cnt(u32)
for pc,label in [(0x58F1,'g567'),(0x5954,'g568-573 NARR?'),(0x596C,'g574'),(0x59A8,'g575-576 NARR'),(0x59D8,'g578-580'),(0x5A16,'g582-588')]:
    chunk=sec1[pc:pc+14]
    print(f"pc=0x{pc:X} ({label}): "+' '.join(f'{b:02X}' for b in chunk))
