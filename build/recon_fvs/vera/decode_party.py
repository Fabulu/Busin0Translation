import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open('build/recon_portrait4/extract/request__ee.bin','rb').read()
KATA_BASE=193
KATA="アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ"
EXTRA={93:'ー',238:'ン',254:'バ',245:'ジ',252:'デ',270:'ェ',273:'ヴ',246:'ズ',247:'ゼ',248:'ゾ',249:'ダ',253:'ド',272:'ッ',
       232:'ラ',267:'?67',268:'?68',289:'?89'}
def k(nv):
    if KATA_BASE<=nv<=KATA_BASE+44: return KATA[nv-KATA_BASE]
    if 95<=nv<=189: return chr((nv-95)+0x20)
    return EXTRA.get(nv,f'<{nv}>')
def decode_at(off,maxw=12):
    s=[]
    for j in range(maxw):
        w=struct.unpack_from('<H',ee,off+j*2)[0]
        if w==0xFFFF: break
        if w==0xFFFE: continue
        s.append(k(w))
    return ''.join(s)

# Leader name at 0x560000 starts with 0001? Actually 0001 then e8 fc 10c. The 0001 might be a count/flag.
print('0x560000:', decode_at(0x560000))
print('0x560002:', decode_at(0x560002))  # skip the leading 0001
print('0x5601f2 (Vera):', decode_at(0x5601f2))

# The leader record likely at 0x560000 with name at +2. Stride between 0x560000 and 0x5601f0?
print('\nstride leader->Vera:', hex(0x5601f0-0x560000))  # 0x1f0 = 496

# Search for more name fields: scan for ffff-terminated kana runs at regular stride
print('\n--- candidate name fields (kana/ascii run >=2 followed by ffff) every where in 0x55f000..0x562000 ---')
base=0x55f000
o=base
while o < 0x562000:
    w=struct.unpack_from('<H',ee,o)[0]
    if 95<=w<=320 and w not in (0xFFFE,):
        # try decode a run
        run=decode_at(o,8)
        # check terminator
        # count chars
        if len(run)>=2 and all(c not in '<' for c in run[:1]):
            nxt=struct.unpack_from('<H',ee,o+len(run.encode('utf-8'))) if False else None
            print(f'  0x{o:08x}: {run}')
            o+=16; continue
    o+=2
