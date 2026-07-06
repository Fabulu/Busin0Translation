import json,struct,glob,os
m=json.load(open('data/msg_glyph_map.json',encoding='utf-8'))
rev={}
for k,v in m.items(): rev.setdefault(v,[]).append(int(k))
# take entry 8193 (res1207) japanese, encode first 6 chars, search file
d=json.load(open('data/type2_dialogue_full.json',encoding='utf-8'))
e=d[8193]
jp=e['japanese']; res=e['resource']
print('res',res,'glyph_count',e['glyph_count'],'jplen',len(jp))
f=glob.glob('extracted/packdata_resources/%04d_*.bin'%res)
print('file',f, 'size', os.path.getsize(f[0]) if f else None)
data=open(f[0],'rb').read()
# build BE pattern from first N chars (only chars with single mapping)
def pack(s):
    out=b''
    for c in s:
        ids=rev.get(c)
        if not ids: return None
        out+=struct.pack('>H',ids[0])
    return out
for n in (4,6,8,10):
    p=pack(jp[:n])
    if p: print('first%d BE found at'%n, hex(data.find(p)))
