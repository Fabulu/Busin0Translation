import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
BASE='C:/programmieren/wizardrytranslation'
ee=open(f'{BASE}/build/recon_portrait4/extract/request__ee.bin','rb').read()
KATA="アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ"
KATA_EXTRA={93:'ー',238:'ン',254:'バ',245:'ジ',252:'デ',270:'ェ',273:'ヴ',246:'ズ',247:'ゼ',248:'ゾ',249:'ダ',253:'ド',272:'ッ'}
def nv(v):
    if 193<=v<=193+44: return KATA[v-193]
    if 95<=v<=189: return chr((v-95)+0x20)
    return KATA_EXTRA.get(v,'?%d?'%v)
def decode_name(off):
    s=''
    for i in range(8):
        v,=struct.unpack_from('<H',ee,off+i*2)
        if v in (0xFFFF,0): break
        s+=nv(v)
    return s
# stride 0x1f0=496. Vera@0x5601f2. Find array start by walking back by 0x1f0
print("=== roster array @ stride 0x1F0 (496B), name at +0 ===")
# walk down from a low base
base=0x5601f2 - 0x1f0*20  # back up
for k in range(40):
    off=base+k*0x1f0
    if 0<=off<len(ee)-16:
        nm=decode_name(off)
        if nm:
            print(f'  slot off=0x{off:08x}: {nm!r}')
