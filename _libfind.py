import struct,glob,os,json
RAW=glob.glob('extracted/packdata_raw/*_type02.raw')
print('type2 raws:',len(RAW))
# menu sequences (msg-glyph IDs) from _lib_cat_seq + decoded title/sub
menus={
 'item_compendium':[193,59,211,225,1289,677],
 'char_directory':[319,412,314,677],
 'adventure_guide':[486,487,136,276,901,118],
 'book_list':[419,412,232,205,212],
 'title_library':[231,194,256,231,232,93],  # ライブラリー  ル? use ラ=231 イ=194 ブ=256 ラ=231 リ=232 ー=93
 'glossary_yougo':[670,1152],  # 用語 (辞典 unmapped)
}
def sec2(data):
    if len(data)<0x1C: return None
    size=struct.unpack_from('<I',data,0x14)[0]; off=struct.unpack_from('<I',data,0x18)[0]
    if off==0 or off>=len(data) or size<4: return None
    return data[off:min(off+size,len(data))]
def pack(ids): return b''.join(struct.pack('>H',g) for g in ids)
results={}
for f in RAW:
    data=open(f,'rb').read(); s2=sec2(data)
    if not s2: continue
    res=int(os.path.basename(f).split('_')[0])
    for name,ids in menus.items():
        p=pack(ids)
        i=s2.find(p)
        if i>=0:
            results.setdefault(name,[]).append((res,i))
for name,h in results.items():
    print('===',name,'===',len(h))
    for res,i in h[:20]: print('  R%d sec2@0x%X'%(res,i))
