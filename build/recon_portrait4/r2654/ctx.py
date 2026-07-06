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
for base in (0x5601f2,0xdc1af2):
    print(f'\n=== context @ 0x{base:x} ===')
    st=base-0x40
    chunk=ee[st:base+0x60]
    print('hex dump (LE u16 from -0x40):')
    for off in range(0,len(chunk),16):
        row=chunk[off:off+16]
        vals=struct.unpack_from('<%dH'%(len(row)//2),row,0)
        chars=''.join(nv(v) if (95<=v<=189 or 193<=v<=237 or v in KATA_EXTRA) else '.' for v in vals)
        print(f'  0x{st+off:08x}: '+' '.join('%04x'%v for v in vals)+'  '+chars)
