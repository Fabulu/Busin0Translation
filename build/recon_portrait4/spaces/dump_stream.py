import sys, json, struct
sys.stdout.reconfigure(encoding='utf-8')
t=json.load(open('data/english_glyph_table.json'))
rev={v:k for k,v in t.items()}
ee=open('build/recon_portrait4/extract/Toolongspaces__ee.bin','rb').read()

def dump(addr,n,tag):
    print(f"\n== {tag} @0x{addr:X} ({n} u16) ==")
    ws=struct.unpack_from(f'>{n}H',ee,addr)
    decoded=''.join(rev.get(w,'{%04X}'%w if w<0xFB00 else '<%04X>'%w) for w in ws)
    print('  glyphs:',' '.join('%04X'%w for w in ws))
    print('  text  :',decoded)
    return ws

# Region containing No one ... the wind
dump(0x11e0a9e-0x10, 90, 'live-sec2 region')
