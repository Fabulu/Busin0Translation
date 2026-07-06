import json
d=json.load(open('data/type2_dialogue_full.json',encoding='utf-8'))
e=d[8193]
print('keys:',list(e.keys()))
for k,v in e.items():
    if k!='japanese': print(k,'=',v)
# print resource fields for all needle#0 and needle#5 entries
needles=['ライブラリー','書物リスト','アイテム図鑑','人物名鑑','用語辞典','冒険の手引き','早送り']
from collections import Counter
res_for=Counter()
for i,e in enumerate(d):
    jp=e.get('japanese','')
    for n in needles:
        if n in jp:
            r=e.get('resource') or e.get('resource_id') or e.get('res') or e.get('file')
            res_for[(needles.index(n),r)]+=1
for (ni,r),c in sorted(res_for.items()):
    print('needle#%d resource=%s count=%d'%(ni,r,c))
