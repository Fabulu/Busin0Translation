import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
# The split-window boundaries (texel): 72,96,144,168,192,216,240,288,312,336,384,432,456,464,504
# UV register stores texel<<4 (12.4). Also dest positions are screen coords.
# Search resource 2880 and EXE for u16 sequences of these texel values or <<4.
RES="extracted/packdata_raw/2880_type11.raw"
data=open(RES,'rb').read()
print(f"R2880 size={len(data)}")
# the line-band UV-Y tops are 0,24,48,...432 ; window widths per line.
# Candidate: a table of (uvX0,uvX1) pairs as u16 texel. Look for 144,168 adjacency.
def find_u16le(seq, label):
    needle=b''.join(struct.pack('<H',v) for v in seq)
    hits=[]
    p=data.find(needle)
    while p>=0 and len(hits)<10:
        hits.append(p); p=data.find(needle,p+1)
    print(f"  u16LE {seq} -> {[hex(h) for h in hits]}")
def find_u16be(seq, label):
    needle=b''.join(struct.pack('>H',v) for v in seq)
    hits=[]
    p=data.find(needle)
    while p>=0 and len(hits)<10:
        hits.append(p); p=data.find(needle,p+1)
    print(f"  u16BE {seq} -> {[hex(h) for h in hits]}")
print("Search for texel boundary pairs (split rows):")
for seq in [[144,168],[192,216],[216,240],[168,456],[216,504],[0,144],[0,192]]:
    find_u16le(seq,'')
    find_u16be(seq,'')
print("Search for <<4 (UV fixed) pairs:")
for seq in [[144*16,168*16],[192*16,216*16],[216*16,504*16]]:
    find_u16le(seq,'')
    find_u16be(seq,'')
