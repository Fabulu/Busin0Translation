import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open('build/recon_portrait4/extract/request__ee.bin','rb').read()
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

# Full roster: start from earliest found name 0x55e102, stride 0x1f0
start=0x55e102
print('Full RAM char roster (idx: addr: name):')
a=start
i=0
while a < 0x562000:
    n=nm(a)
    print(f'  {i:2d}: 0x{a:08x}: {n}')
    a+=0x1f0; i+=1
