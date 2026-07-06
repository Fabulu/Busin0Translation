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
# Active party Vera copy at 0x5601f2 is in the 0x1F0-stride ROSTER (0x55dxxx..0x561xxx).
# That roster IS the active char db. The party-bar reads from it. Confirm record 0x5601f2 stat block
# to prove it's a live character record (has HP/level), proving names come from this savegame-loaded db.
off=0x5601f2
print('Vera record @0x%x:'%off)
print('  name:', ''.join(nv(v) for v in struct.unpack_from('<4H',ee,off)))
# dump record
for o in range(off-2, off+0x40,16):
    vals=struct.unpack_from('<8H',ee,o)
    print(f'  0x{o:08x}: '+' '.join('%04x'%v for v in vals))
# The HP value 0x01f4=500 we saw earlier at +0x40 region. Confirm.
