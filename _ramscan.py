import struct
ram=open('runs/CLAUDE-RUNS/RUN-20260623-1835-box-request-formatting/subagents/untranslatedlibrary/eeMemory.bin','rb').read()
print('RAM size',len(ram))
# SJIS forms
sjis={'ITEMZUKAN':'アイテム図鑑','JINBUTSU':'人物名鑑','YOUGO':'用語辞典','SHOMOTSU':'書物リスト','LIBRARY':'ライブラリー','HAYAOKURI':'早送り'}
for k,v in sjis.items():
    b=v.encode('cp932')
    i=ram.find(b); cnt=ram.count(b)
    print('SJIS',k, 'count',cnt, ('@0x%X'%i if i>=0 else ''))
# UTF16LE/BE
for k,v in sjis.items():
    for enc in ('utf-16-le','utf-16-be'):
        b=v.encode(enc); i=ram.find(b)
        if i>=0: print('UTF',enc,k,'@0x%X'%i)
