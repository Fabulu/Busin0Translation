import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open('build/recon_portrait4/extract/request__ee.bin','rb').read()
raw=open('build/recon_fvs/vera/r2654_from_v92iso.raw','rb').read()
prist=open('extracted/packdata_raw/2654_type44.raw','rb').read()

# Is R2654 loaded ANYWHERE in RAM verbatim (BE u16)? search for the sub7 offset-table header signature
# sub7 starts: count=47 (0x002f), pad 0000, then offsets. fingerprint = bytes at sub7 start
def hdr(r): return [dict(zip(('sub','size','off','z'), struct.unpack_from('<4I', r, i*16))) for i in range(44)]
H=hdr(raw)
h7=next(x for x in H if x['sub']==7)
sig7=raw[h7['off']:h7['off']+24]
print('searching sub7 sig (v92 romanized) in RAM:', ee.find(sig7))

Hp=hdr(prist)
h7p=next(x for x in Hp if x['sub']==7)
sig7p=prist[h7p['off']:h7p['off']+24]
print('searching sub7 sig (pristine kata) in RAM:', ee.find(sig7p))

# sub8 sig
h8=next(x for x in Hp if x['sub']==8)
sig8=prist[h8['off']:h8['off']+24]
print('searching sub8 sig in RAM:', ee.find(sig8))

# Search for the WHOLE R2654 TOC header (44 subs * 16 bytes) loaded into RAM
toc_sig = raw[0:64]
print('searching R2654 TOC header in RAM:', ee.find(toc_sig))

# The RAM names are byte-swapped LE. Maybe a name TABLE separate from bios.
# Each RAM name appears alone (no bio). Look: is there a contiguous LE name table somewhere?
# Vera at 0x5601f2 is INSIDE a 0x1f0-stride record array (char bios in RAM).
# Find the RECORD BASE: the field before name. Vera name 0x5601f2, record likely starts at a round offset.
# stride 0x1f0=496. start of array? backtrack: 0x5601f2 - n*0x1f0 until name junk.
# We found names at 0x55fa32 (Yokkun) up. Let me find the FIRST record.
# Print the bytes 0x40 before each name to see record header / ID.
KATA_BASE=193
KATA="アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ"
EXTRA={93:'ー',238:'ン',254:'バ',245:'ジ',252:'デ',270:'ェ',273:'ヴ',246:'ズ',247:'ゼ',248:'ゾ',249:'ダ',253:'ド',272:'ッ',232:'ラ'}
def k(nv):
    if KATA_BASE<=nv<=KATA_BASE+44: return KATA[nv-KATA_BASE]
    if 95<=nv<=189: return chr((nv-95)+0x20)
    return EXTRA.get(nv,f'<{nv}>')
def nm(a):
    s=[]
    for j in range(12):
        w=struct.unpack_from('<H',ee,a+j*2)[0]
        if w==0xFFFF: break
        if w==0xFFFE: continue
        s.append(k(w))
    return ''.join(s)
# record header: read u16 at name-0x?? . Show record for Vera: dump 0x10 before name
print('\nVera record header (name-0x10 .. name):')
for o in range(0x5601f2-0x10, 0x5601f2+2, 2):
    print(f'  0x{o:08x}: {struct.unpack_from("<H",ee,o)[0]:04x}')
# Is there an index/ID byte distinguishing recruited vs not?
