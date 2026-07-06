import glob,os
targets={
 'LIBRARY':'ライブラリー',
 'ITEMZUKAN':'アイテム図鑑',
 'JINBUTSU':'人物名鑑',
 'YOUGO':'用語辞典',
 'BOUKEN':'冒険の手引き',
 'SHOMOTSU':'書物リスト',
 'HAYAOKURI':'早送り',
}
pats={}
for k,v in targets.items():
    try: pats[k]=v.encode('cp932')
    except: pass
# scan EXE first
exe=open('extracted/SLPM_653.78','rb').read() if os.path.exists('extracted/SLPM_653.78') else None
import glob as g
exefiles=g.glob('extracted/SLPM*')
print('exe candidates',exefiles)
for ef in exefiles:
    data=open(ef,'rb').read()
    for k,p in pats.items():
        i=data.find(p)
        if i>=0: print(f'EXE {os.path.basename(ef)}: {k} @0x{i:X}')
