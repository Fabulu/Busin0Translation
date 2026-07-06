# -*- coding: utf-8 -*-
import json
def load(f): return json.load(open(f,encoding='utf-8'))
def find(d,res,msg):
    for r in d:
        if str(r.get('resource'))==str(res) and str(r.get('message',r.get('msg_index')))==str(msg):
            return r
    return None
import unicodedata
def romaji_hint(jp):
    # ASCII-safe: show codepoint names is too long; just give char count + a transliteration of kana? 
    # Instead, output the raw via unicode escape so orchestrator can read; but we need ascii summary.
    return jp.encode('unicode_escape').decode()

targets=[
 ('data/translate_chunks/chunk_04_translated.json',[('41','1'),('41','2'),('40','1'),('40','29'),('42','1'),('42','2'),('42','5'),('42','7')]),
 ('data/translate_chunks/chunk_r43_fix.json',[('43','9'),('43','22')]),
 ('data/type2_translated/batch_05.json',[('1206','134'),('1206','209'),('1206','210'),('1206','221'),('1206','123'),('1207','392')]),
 ('data/type2_translated/batch_08.json',[('1212','30'),('1212','180')]),
 ('data/type2_translated/batch_gap1347.json',[('1347','4')]),
 ('data/type2_translated/batch_02.json',[('1202','75'),('1202','85'),('1202','152'),('1200','141'),('1201','45')]),
 ('data/type2_translated/batch_r39_equip_b.json',[('39','415')]),
]
out={}
for f,ms in targets:
    d=load(f)
    for res,msg in ms:
        r=find(d,res,msg)
        if r:
            out[f"{f}|R{res}_M{msg}"]={'en':r.get('english'),'jp_esc':romaji_hint(r.get('japanese',''))}
with open('build/_shard0_detail.json','w',encoding='utf-8') as w:
    json.dump(out,w,ensure_ascii=False,indent=1)
for k,v in out.items():
    print('==',k)
    print('  EN:',v['en'].encode('ascii','replace').decode())
    print('  JP:',v['jp_esc'])
