# -*- coding: utf-8 -*-
import json,glob,os,re
# Hunt consumables/materials/keys in md_import (non-R34) and all batches for item-noun names
files=['data/translate_chunks/chunk_md_import.json','data/type2_translated/batch_md_import.json']
itemkw=re.compile(r'(potion|herb|antidote|elixir|cure|stone|gem|crystal|ore|shard|fragment|powder|chip|fang|claw|scale|horn|feather|bone|medal|coin|seal|key|ticket|scroll|tome|spellbook|spell book|water|oil|ash|root|seed|soul|spirit|essence|blood|tear|amulet|talisman|charm|knife|knives)',re.I)
out=[]
for f in files:
    d=json.load(open(f,encoding='utf-8'))
    for rec in d:
        res=str(rec.get('resource'))
        if res=='34': continue
        e=(rec.get('english') or '').strip()
        if not e or '/' in e or '[' in e or '"' in e: continue
        if e.endswith(('.','!','?')): continue
        if len(e.split())>5: continue
        if not itemkw.search(e): continue
        if len(e)<=12: continue
        out.append((os.path.basename(f),res,rec.get('message',rec.get('msg_index')),e,len(e)))
seen=set();uniq=[]
for x in out:
    k=(x[1],x[3])
    if k in seen: continue
    seen.add(k);uniq.append(x)
with open('build/scan4e_out.txt','w',encoding='utf-8') as w:
    for f,res,m,e,n in sorted(uniq,key=lambda x:(x[1],-x[4])):
        w.write('%-28s R%-5s m%-6s %2d %s\n'%(f,res,m,n,e))
print(len(uniq))
