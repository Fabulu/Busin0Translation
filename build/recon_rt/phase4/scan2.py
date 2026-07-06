import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open('build/recon_tri/extract/requestbroken__ee.bin','rb').read()
sys.path.insert(0,'tools')
from patch_section1_offsets import group_choice_markers

# Build the injected R1197 sec2 and search for a unique injected group's glyph run in RAM.
# Use the injected file we produced.
inj=open('build/recon_rt/phase4/out/1197_type02.raw','rb').read()
s2sz=struct.unpack_from('<I',inj,0x14)[0]; s2o=struct.unpack_from('<I',inj,0x18)[0]
sec2=inj[s2o:s2o+s2sz]
n=len(sec2)//2
words=[struct.unpack_from('>H',sec2,i*2)[0] for i in range(n)]
groups=[];cur=[]
for w in words:
    if w==0xFFFF: groups.append(cur);cur=[]
    else: cur.append(w)

# Take choice group g63 injected glyph stream as BE bytes, search RAM
def grp_bytes(gi):
    return b''.join(struct.pack('>H',w) for w in groups[gi])
for gi in [63,620,652]:
    pat=grp_bytes(gi)
    idx=ee.find(pat)
    print(f'g{gi} ({len(groups[gi])} words) found in EE RAM at: {hex(idx) if idx>=0 else "NOT FOUND"}')
    if idx>=0:
        # confirm markers in RAM copy
        ram=ee[idx:idx+len(pat)]
        rw=[struct.unpack_from('>H',ram,i*2)[0] for i in range(len(ram)//2)]
        print('   RAM markers:', [hex(x) for x in group_choice_markers(rw)])

# Also: is the full injected sec2 (or a big chunk) present? search for a long unique run from g905 barkeep
# search a 40-byte chunk from group 8 (request text)
chunk=grp_bytes(63)[:24]
print('whole-resource presence: g63 head found at', hex(ee.find(chunk)))
