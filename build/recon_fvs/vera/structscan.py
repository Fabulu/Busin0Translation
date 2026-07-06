import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open('build/recon_portrait4/extract/request__ee.bin','rb').read()
KATA="アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ"
KATA_EXTRA={93:'ー',238:'ン',254:'バ',245:'ジ',252:'デ',270:'ェ',273:'ヴ',246:'ズ',247:'ゼ',248:'ゾ',249:'ダ',253:'ド',272:'ッ',239:'<sa?>',243:'<so?>'}
def k(nv):
    if 193<=nv<=237: return KATA[nv-193]
    if nv==238: return 'ン'
    return KATA_EXTRA.get(nv,f'<{nv}>')
def name_at(p):
    s=''
    for q in range(p,p+40,2):
        w=struct.unpack_from('<H',ee,q)[0]
        if w==0xFFFF: break
        if w==0: break
        if 95<=w<=189: s+=chr(w-95+0x20)
        else: s+=k(w)
    return s
# Look for the name-table region. Each char struct in 0x560xxx region.
# 0x5601F2 is one member. Find other party member names near it by scanning for 0x011x or ascii at fixed stride
print('=== region 0x55F000..0x562000 name runs (LE, start with kata or ascii) ===')
base=0x55F000
p=base
while p<0x563000:
    w=struct.unpack_from('<H',ee,p)[0]
    # plausible name start: ascii cap 128-153 or kata 193+
    if (128<=w<=153) or (193<=w<=273):
        nm=name_at(p)
        if len(nm)>=2 and not nm.startswith('<'):
            print('  0x%X: %r'%(p,nm))
            p+=2
            continue
    p+=2
