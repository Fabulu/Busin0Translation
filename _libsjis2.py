import glob,os
targets={
 'ITEMZUKAN':'アイテム図鑑',
 'JINBUTSU':'人物名鑑',
 'YOUGO':'用語辞典',
 'BOUKEN':'冒険の手引き',
 'SHOMOTSU':'書物リスト',
 'LIBRARY':'ライブラリー',
}
pats={k:v.encode('cp932') for k,v in targets.items()}
files=sorted(glob.glob('extracted/packdata_resources/*.bin'))
hits={}
for f in files:
    data=open(f,'rb').read()
    for k,p in pats.items():
        if p in data:
            hits.setdefault(k,[]).append((os.path.basename(f),data.find(p)))
for k,h in hits.items():
    print('===',k,'==='); 
    for fn,i in h: print(f'  {fn} @0x{i:X}')
if not hits: print('NO SJIS HITS in resources')
