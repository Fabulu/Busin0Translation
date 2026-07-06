import struct,glob,os,json,itertools
m=json.load(open('data/msg_glyph_map.json',encoding='utf-8'))
rev={}
for k,v in m.items(): rev.setdefault(v,[]).append(int(k))
menus={'item_compendium':'アイテム図鑑','char_directory':'人物名鑑','adventure_guide':'冒険の手引き','book_list':'書物リスト','title_library':'ライブラリー'}
def patterns(s):
    opts=[rev.get(c,[]) for c in s]
    if any(not o for o in opts): 
        # use only the prefix up to first unmapped
        opts=[]
        for c in s:
            o=rev.get(c)
            if not o: break
            opts.append(o)
    if not opts: return []
    res=[]
    for combo in itertools.product(*opts):
        res.append(b''.join(struct.pack('>H',g) for g in combo))
    return res
def sec2(data):
    if len(data)<0x1C: return None
    size=struct.unpack_from('<I',data,0x14)[0]; off=struct.unpack_from('<I',data,0x18)[0]
    if off==0 or off>=len(data) or size<4: return None
    return data[off:min(off+size,len(data))]
pats={n:patterns(s) for n,s in menus.items()}
from collections import defaultdict
found=defaultdict(dict)
for f in glob.glob('extracted/packdata_raw/*.raw'):
    data=open(f,'rb').read(); res=int(os.path.basename(f).split('_')[0])
    blobs=[]
    s2=sec2(data); 
    if s2: blobs.append(('s2',s2))
    blobs.append(('file',data))
    for tag,blob in blobs:
        for n,plist in pats.items():
            for p in plist:
                i=blob.find(p)
                if i>=0:
                    found[res].setdefault(n,(tag,i)); break
for res in sorted(found):
    if len(found[res])>=2:
        print('R%d (%d items):'%(res,len(found[res])), {k:'%s@0x%X'%(v[0],v[1]) for k,v in found[res].items()})
