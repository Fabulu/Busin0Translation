import sys, json, struct, glob, os
sys.stdout.reconfigure(encoding='utf-8')
t=json.load(open('data/english_glyph_table.json'))
def enc(s): return b''.join(struct.pack('>H',t.get(c,t.get(c.lower(),31))) for c in s)
pat=enc('No one')
for d in ['build/packdata_resources','build/patched_type2','extracted/packdata_raw']:
    for p in sorted(glob.glob(d+'/*type02.raw')):
        data=open(p,'rb').read()
        if pat in data:
            i=data.find(pat)
            print(os.path.basename(p), d, 'off=0x%X'%i)
