import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open('build/recon_portrait4/extract/request__ee.bin','rb').read()
KATA="アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ"
EX={93:'ー',238:'ン',254:'バ',245:'ジ',252:'デ',270:'ェ',273:'ヴ',246:'ズ',247:'ゼ',248:'ゾ',249:'ダ',253:'ド',272:'ッ',239:'サ',240:'シ',241:'チ',242:'ツ',243:'ト',262:'シ',265:'ー',267:'ィ',268:'カ'}
def k(nv):
    if 193<=nv<=237: return KATA[nv-193]
    return EX.get(nv,f'<{nv}>')
def name_at(p):
    s=''
    for q in range(p,p+40,2):
        w=struct.unpack_from('<H',ee,q)[0]
        if w in (0xFFFF,0): break
        if 95<=w<=189: s+=chr(w-95+0x20)
        else: s+=k(w)
    return s
# stride 0x1F0 starting from Vera, walk both directions
stride=0x1F0
vera=0x5601F2
print('stride 0x%X = %d bytes'%(stride,stride))
print('=== table walk (name field at struct+0) ===')
for i in range(-3,30):
    p=vera+i*stride
    if p<0 or p+0x40>len(ee): continue
    nm=name_at(p)
    # struct base = p (name at offset 0)
    # show a few following fields
    f=[struct.unpack_from('<H',ee,p+0x10+j*2)[0] for j in range(8)]
    print('  idx %2d  base=0x%X  name=%-14r  fields@+0x10=%s'%(i,p,nm,f))
