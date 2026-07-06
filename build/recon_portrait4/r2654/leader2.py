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
# The ACTIVE PARTY (not roster) — leader 'A A' + Vera. Active party records hold current members.
# Vera active copy at 0xdc1af2 (high RAM). Look for leader near it / preceding record.
# Active party records often a small fixed array. Dump region 0xdc1800..0xdc1c00
print('=== active party region near 0xdc1af2 ===')
for off in range(0xdc1880,0xdc1b00,16):
    vals=struct.unpack_from('<8H',ee,off)
    chars=''.join(nv(v) if (95<=v<=189 or 193<=v<=237 or v in KATA_EXTRA) else '.' for v in vals)
    print(f'  0x{off:08x}: '+' '.join('%04x'%v for v in vals)+'  '+chars)
# 'A A' leader: name_val for 'A'=128. As LE u16 store: a name field = 128,? Look for 0x0080 starting a name
print('\n=== search 0x0080 (A) as first name slot, with following pattern in active party ===')
import struct as st
# leader may be ascii 'A A' = vals 128, space?, 128. Space could be 0x0000 (glyph 0x0000)
for off in range(0xdc1000,0xdc2000,2):
    v0,v1,v2=struct.unpack_from('<3H',ee,off)
    if v0==128 and v2==128 and v1 in (0,95,128):
        print(f'  0x{off:08x}: {v0:04x} {v1:04x} {v2:04x}  -> A?A')
