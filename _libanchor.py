import glob,os,struct
def pat(ids): return b''.join(struct.pack('>H',g) for g in ids)
anchors={
 'JINBUTSU_319_412':[319,412],
 'ZUKAN_1289_677':[1289,677],
 'YOUGO_670_1152':[670,1152],
 'YOUGO_881_1152':[881,1152],
}
files=sorted(glob.glob('extracted/packdata_resources/*.bin'))
for name,ids in anchors.items():
    p=pat(ids); hits=[]
    for f in files:
        data=open(f,'rb').read()
        i=data.find(p)
        if i>=0: hits.append((os.path.basename(f),i,len(data)))
    print('===',name,'===', len(hits),'hits')
    for fn,i,ln in hits[:15]: print('  %s @0x%X filelen %d'%(fn,i,ln))
