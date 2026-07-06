import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
BASE='C:/programmieren/wizardrytranslation'
ee=open(f'{BASE}/build/recon_portrait4/extract/request__ee.bin','rb').read()
KATA="アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ"
KATA_EXTRA={93:'ー',238:'ン',254:'バ',245:'ジ',252:'デ',270:'ェ',273:'ヴ',246:'ズ',247:'ゼ',248:'ゾ',249:'ダ',253:'ド',272:'ッ'}
def nv(v):
    if 193<=v<=193+44: return KATA[v-193]
    if 95<=v<=189: return chr((v-95)+0x20)
    return KATA_EXTRA.get(v,'')
def decode_name(off):
    vals=struct.unpack_from('<8H',ee,off)
    s=''
    for v in vals:
        if v==0xFFFF or v==0: break
        c=nv(v)
        s+= c if c else '?%d?'%v
    return s
# Vera record name @ 0x5601f2. Scan a window for other name-like fields at regular strides.
# Look at region 0x55f000 .. 0x562000, print any 8-u16 run that decodes to >=1 name char then FFFF/0
print('scanning 0x55f000..0x562000 for name fields:')
for off in range(0x55f000,0x562000,2):
    v0,=struct.unpack_from('<H',ee,off)
    # name char first slot in valid ranges
    if (95<=v0<=189 or 193<=v0<=237 or v0 in KATA_EXTRA):
        nxt,=struct.unpack_from('<H',ee,off+8*2)
        s=decode_name(off)
        if 2<=len(s)<=8:
            # check it's terminated
            term=struct.unpack_from('<H',ee,off+len(s)*2)[0] if off+len(s)*2+2<=len(ee) else 0
            if term in (0xFFFF,0,0xe7):
                print(f'  0x{off:08x}: {s!r}')
