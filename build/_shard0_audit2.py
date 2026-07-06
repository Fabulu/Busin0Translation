# -*- coding: utf-8 -*-
import json, os, re

SHARD_FILES = [
 'data/translate_chunks/chunk_01_translated.json',
 'data/translate_chunks/chunk_04_translated.json',
 'data/translate_chunks/chunk_07_translated.json',
 'data/translate_chunks/chunk_r34_fix.json',
 'data/translate_chunks/chunk_r37_extra.json',
 'data/translate_chunks/chunk_r38_fix_no_gender.json',
 'data/translate_chunks/chunk_r43_fix.json',
 'data/type2_translated/batch_02.json',
 'data/type2_translated/batch_05.json',
 'data/type2_translated/batch_08.json',
 'data/type2_translated/batch_11.json',
 'data/type2_translated/batch_gap1347.json',
 'data/type2_translated/batch_intro_narration.json',
 'data/type2_translated/batch_r1168_1173.json',
 'data/type2_translated/batch_r39_equip_b.json',
]
def jp_len(s): return sum(1 for c in s if ord(c)>0x2000)

# business / what-business style + short barker prompts
BIZ = re.compile(r"business|what (do|are|brings|can i)|what'?s your|how can i help|may i help|need (something|anything)|looking for|what'?ll it be|what is it|state your|your purpose|come (back|again)|farewell|welcome|good luck|anything else|are you (sure|done|ready|leaving)|do you (wish|want|need)|would you|shall i|leave\??$", re.I)

out=[]
for f in SHARD_FILES:
    if not os.path.exists(f): continue
    d=json.load(open(f,encoding='utf-8'))
    if not isinstance(d,list): continue
    for rec in d:
        en=rec.get('english')
        if not en or not isinstance(en,str): continue
        jp=rec.get('japanese','')
        en_s=en.strip()
        if BIZ.search(en_s) and len(en_s)>0:
            key=f"R{rec.get('resource')}_M{rec.get('message',rec.get('msg_index'))}"
            out.append((f,key,en_s,jp,jp_len(jp),len(en_s)))
print("BIZ-MATCHES",len(out))
with open('build/_shard0_biz.json','w',encoding='utf-8') as w:
    json.dump([{'file':o[0],'key':o[1],'en':o[2],'jp':o[3],'jp_len':o[4],'en_len':o[5]} for o in out],w,ensure_ascii=False,indent=1)
for o in out:
    safe=o[2].encode('ascii','replace').decode()
    print(f"{o[5]:3d}/{o[4]:2d} {o[1]:14s} {os.path.basename(o[0])[:18]:18s} {safe[:65]}")
