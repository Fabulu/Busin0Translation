import struct,glob,os,json
m=json.load(open('data/msg_glyph_map.json',encoding='utf-8'))
rev={}
for k,v in m.items(): rev.setdefault(v,[]).append(int(k))
menus={
 'item_compendium':[193,59,211,225,1289,677],
 'char_directory':[319,412,314,677],
 'adventure_guide':[486,487,136,276,901,118],
 'book_list':[419,412,232,205,212],
 'title_library':[231,194,256,231,232,93],
}
def pack(ids): return b''.join(struct.pack('>H',g) for g in ids)
def sec2(data):
    if len(data)<0x1C: return None
    size=struct.unpack_from('<I',data,0x14)[0]; off=struct.unpack_from('<I',data,0x18)[0]
    if off==0 or off>=len(data) or size<4: return None
    return data[off:min(off+size,len(data))]
# scan ALL resources, both raw type2 sec2 AND whole-file (for type01)
from collections import defaultdict
found=defaultdict(set)  # res -> set(menu names)
allraw=glob.glob('extracted/packdata_raw/*.raw')
for f in allraw:
    data=open(f,'rb').read()
    res=int(os.path.basename(f).split('_')[0])
    # try sec2
    blobs=[]
    s2=sec2(data)
    if s2: blobs.append(s2)
    blobs.append(data)  # whole file fallback
    for blob in blobs:
        for name,ids in menus.items():
            if pack(ids) in blob:
                found[res].add(name)
# resources with >=3 menu items = strong UI candidate
for res in sorted(found):
    if len(found[res])>=3:
        print('R%d : %s'%(res, sorted(found[res])))
