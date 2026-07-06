import sys, json, struct
sys.stdout.reconfigure(encoding='utf-8')
t=json.load(open('data/english_glyph_table.json'))
def enc(s):
    out=bytearray()
    for ch in s:
        g=t.get(ch, t.get(ch.lower(),31))
        out+=struct.pack('>H',g)
    return bytes(out)

ee=open('build/recon_portrait4/extract/Toolongspaces__ee.bin','rb').read()
print("ee len",len(ee))

# search for "No one" both BE u16 and possible other forms
for label,pat in [
    ('BE-u16 "No one"', enc('No one')),
    ('BE-u16 "No"', enc('No')),
    ('BE-u16 "sight"', enc('sight')),
    ('BE-u16 "the wind"', enc('the wind')),
    ('LE-u16 "No one"', b''.join(struct.pack('<H',t.get(c,t.get(c.lower(),31))) for c in 'No one')),
    ('bytes ascii "No one"', b'No one'),
    ('bytes-glyphid "No one"', bytes(t.get(c,t.get(c.lower(),31)) for c in 'No one')),
]:
    idxs=[]
    start=0
    while True:
        i=ee.find(pat,start)
        if i<0: break
        idxs.append(i); start=i+1
        if len(idxs)>20: break
    print(f"{label}: {len(idxs)} hits", [hex(i) for i in idxs[:10]])
