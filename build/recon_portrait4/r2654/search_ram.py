import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
BASE='C:/programmieren/wizardrytranslation'
ee=open(f'{BASE}/build/recon_portrait4/extract/request__ee.bin','rb').read()
print('EE size',len(ee))

# Vera katakana name-value run BE u16: 273,270,93,231 (+ maybe FFFE)
def be(vals): return b''.join(struct.pack('>H',v) for v in vals)
def le(vals): return b''.join(struct.pack('<H',v) for v in vals)

patterns = {
 'Vera_kana_BE_u16': be([273,270,93,231]),
 'Vera_kana_LE_u16': le([273,270,93,231]),
 'Vera_kana_BE_2v': be([273,270]),
 'Vera_romaji_nv_BE': be([149,164,177,160]),  # patched name-value run
 'Vera_ascii': b'Vera',
 'Vera_ascii_wide_LE': 'Vera'.encode('utf-16-le'),
}
# Also raw bytes single: name-values may be stored as bytes not u16
patterns['Vera_kana_bytes']=bytes([273-256 if v>255 else v for v in []]) or b''  # skip

for name,pat in patterns.items():
    if not pat: continue
    idxs=[]
    s=0
    while True:
        i=ee.find(pat,s)
        if i<0: break
        idxs.append(i); s=i+1
        if len(idxs)>40: break
    print(f'{name} ({pat.hex()}): {len(idxs)} hits -> '+', '.join('0x%x'%i for i in idxs[:20]))
