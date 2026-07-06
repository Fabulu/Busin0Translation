import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open('build/recon_portrait4/extract/request__ee.bin','rb').read()
def be(words): return b''.join(struct.pack('>H',w) for w in words)
def le(words): return b''.join(struct.pack('<H',w) for w in words)
# Does R2654 sub7 (BE) appear in RAM anywhere? signature: entry1 Aurora BE 193,195,235,93,231
sig_be_aurora=be([193,195,235,93,231])
sig_le_aurora=le([193,195,235,93,231])
# R2654 sub7 raw offset table starts with count=47=0x002F BE then 0x0000
sub7_sig=bytes.fromhex('002f0000')
for nm,pat in [('BE Aurora(R2654 raw)',sig_be_aurora),('LE Aurora',sig_le_aurora),('sub7 hdr 002f0000',sub7_sig)]:
    i=ee.find(pat); hits=[]
    while i!=-1 and len(hits)<10:
        hits.append(i); i=ee.find(pat,i+1)
    print(nm, len(hits),['0x%X'%x for x in hits])
# Konde LE 202,238,252
for nm,pat in [('LE Konde',le([202,238,252])),('LE Iris 194,93,232,205',le([194,93,232,205]))]:
    i=ee.find(pat); hits=[]
    while i!=-1 and len(hits)<20:
        hits.append(i); i=ee.find(pat,i+1)
    print(nm, len(hits),['0x%X'%x for x in hits])
