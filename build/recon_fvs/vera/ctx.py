import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open('build/recon_portrait4/extract/request__ee.bin','rb').read()
KATA="アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ"
KATA_EXTRA={93:'ー',238:'ン',254:'バ',245:'ジ',252:'デ',270:'ェ',273:'ヴ',246:'ズ',247:'ゼ',248:'ゾ',249:'ダ',253:'ド',272:'ッ'}
def k(nv):
    if 193<=nv<=237: return KATA[nv-193]
    return KATA_EXTRA.get(nv,f'<{nv}>')
for addr in (0x5601F2,0xDC1AF2):
    print('=== context @0x%X ==='%addr)
    st=addr-0x60
    raw=ee[st:addr+0x60]
    print('hex:', raw.hex())
    # decode as LE u16 around region
    print('-- LE u16 words from -0x20 to +0x30 --')
    for p in range(addr-0x20,addr+0x30,2):
        w=struct.unpack_from('<H',ee,p)[0]
        mark=' <<<' if p==addr else ''
        ch=k(w) if (95>w or w>0xFF) and w!=0 else ''
        print('  0x%X: %5d 0x%04X %s%s'%(p,w,w,ch,mark))
