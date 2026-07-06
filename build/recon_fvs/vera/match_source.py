import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open('build/recon_portrait4/extract/request__ee.bin','rb').read()
raw=open('build/recon_fvs/vera/r2654_from_v92iso.raw','rb').read()
prist=open('extracted/packdata_raw/2654_type44.raw','rb').read()
KATA_BASE=193
KATA="アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ"
EXTRA={93:'ー',238:'ン',254:'バ',245:'ジ',252:'デ',270:'ェ',273:'ヴ',246:'ズ',247:'ゼ',248:'ゾ',249:'ダ',253:'ド',272:'ッ',232:'ラ'}
def k(nv):
    if KATA_BASE<=nv<=KATA_BASE+44: return KATA[nv-KATA_BASE]
    if 95<=nv<=189: return chr((nv-95)+0x20)
    return EXTRA.get(nv,f'<{nv}>')

# Build RAM roster: records stride 0x1f0, name at record_base+? 
# Vera name at 0x5601f2. Erika at 0x5603e2. diff 0x1f0. So name offset within record = 0x1f2 from a base where base+0x1f0=next.
# record base for Vera = 0x5601f2 - X. Let's just read names at 0x5601f2 + n*0x1f0 going backwards/forwards.
name0 = 0x5601f2
recs=[]
# go backwards to find start
start=name0
while start-0x1f0 >= 0x55e000:
    start-=0x1f0
print('RAM roster (LE u16 names, stride 0x1f0):')
ram_names=[]
a=start
for n in range(40):
    s=[]
    for j in range(12):
        w=struct.unpack_from('<H',ee,a+j*2)[0]
        if w==0xFFFF: break
        if w==0xFFFE: continue
        s.append(k(w))
    nm=''.join(s)
    if nm.strip('<>0 '):
        print(f'  0x{a:08x}: {nm}')
        ram_names.append(nm)
    a+=0x1f0
    if a > 0x562000: break

# Now decode sub7, sub8, sub33 entry-by-entry (already have sub7). Decode sub8/sub33 as offset-table subs.
def decode_sub(raw, off, size, label):
    cnt=struct.unpack_from('>H',raw,off)[0]
    print(f'\n{label}: off=0x{off:x} count={cnt}')
    offs=[struct.unpack_from('>H',raw,off+4+i*4)[0] for i in range(cnt)]
    names=[]
    for i in range(cnt):
        st=off+offs[i]; en=off+(offs[i+1] if i+1<cnt else size)
        seg=raw[st:en]
        words=[struct.unpack_from('>H',seg,p)[0] for p in range(0,len(seg)-1,2)]
        s=[]
        for w in words:
            if w==0xFFFF: break
            if w==0xFFFE: continue
            s.append(k(w))
        names.append(''.join(s))
    return names

def hdr(raw):
    return [dict(zip(('sub','size','off','z'), struct.unpack_from('<4I', raw, i*16))) for i in range(44)]
H=hdr(prist)
for subn in (7,8,33):
    h=next(x for x in H if x['sub']==subn)
    nms=decode_sub(prist,h['off'],h['size'],f'PRISTINE sub{subn}')
    for i,nm in enumerate(nms[:50]):
        print(f'   {i:2d}: {nm}')
