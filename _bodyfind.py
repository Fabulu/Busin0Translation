import struct,glob,os,json
def pack(ids): return b''.join(struct.pack('>H',g) for g in ids)
anchors={
 'akusesari':[193,200,206,203,232,93],   # アクセサリー
 'touhan':[212,269,93,218,238],          # トゥーハン
}
def sec2(data):
    if len(data)<0x1C: return None
    size=struct.unpack_from('<I',data,0x14)[0]; off=struct.unpack_from('<I',data,0x18)[0]
    if off==0 or off>=len(data) or size<4: return None
    return data[off:min(off+size,len(data))]
for f in glob.glob('extracted/packdata_raw/*.raw'):
    data=open(f,'rb').read(); res=int(os.path.basename(f).split('_')[0])
    s2=sec2(data); blobs=[('file',data)]
    if s2: blobs=[('s2',s2),('file',data)]
    for tag,blob in blobs:
        for name,ids in anchors.items():
            i=blob.find(pack(ids))
            if i>=0:
                print('R%d %s %s @0x%X'%(res,name,tag,i))
