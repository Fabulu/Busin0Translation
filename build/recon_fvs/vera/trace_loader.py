import sys, struct, json
sys.stdout.reconfigure(encoding='utf-8')
ee=open('build/recon_portrait4/extract/request__ee.bin','rb').read()

anchor = bytes([0x01,0xc0,0x11,0x01,0x0e,0x01,0x5d,0x00,0xe7,0x00])
i=ee.find(anchor); occ=[]
while i!=-1:
    occ.append(i); i=ee.find(anchor,i+1)
print('anchor (01c0 + kata Vera) hits:', [hex(x) for x in occ])

gt=json.load(open('data/english_glyph_table.json',encoding='utf-8'))
gidA = gt.get('A', gt.get('a'))
print('glyph A gid:', gidA, '-> name_val', (gidA+95) if gidA is not None else None)

print('\n--- region 0x560000..0x560400 nonzero LE u16 ---')
for o in range(0x560000,0x560400,2):
    w=struct.unpack_from('<H',ee,o)[0]
    if w!=0:
        kana=''
        if 193<=w<=237: kana=chr(0x30a2+(w-193)) if w<=237 else ''
        print(f'  0x{o:08x}: {w:04x} ({w})')
