import json
d=json.load(open('data/type2_dialogue_full.json',encoding='utf-8'))
print('top type:',type(d))
# find entries containing the needles
needles=['ライブラリー','アイテム図鑑','人物名鑑','用語辞典','冒険の手引き','書物リスト','早送り']
def walk(o,path=''):
    if isinstance(o,dict):
        for k,v in o.items(): walk(v,path+'/'+str(k))
    elif isinstance(o,list):
        for i,v in enumerate(o): walk(v,path+'[%d]'%i)
    elif isinstance(o,str):
        for n in needles:
            if n in o:
                print('PATH',path,'needle#',needles.index(n))
walk(d)
