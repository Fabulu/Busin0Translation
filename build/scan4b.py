# -*- coding: utf-8 -*-
import json,glob,os,re

files = (['data/translate_chunks/chunk_r35_menus_fix.json',
          'data/translate_chunks/chunk_r36_translated.json',
          'data/translate_chunks/chunk_r37_extra.json',
          'data/translate_chunks/chunk_r37_r48_r49_translated.json',
          'data/translate_chunks/chunk_r40_r42_translated.json',
          'data/translate_chunks/chunk_r43_fix.json',
          'data/translate_chunks/chunk_r43_r45_translated.json']
         + sorted(glob.glob('data/translate_chunks/chunk_0*_translated.json'))
         + sorted(glob.glob('data/type2_translated/*.json')))
files=[f for f in files if 'chunk_00' not in f]

def name_like(e):
    if not e or not isinstance(e,str): return None
    e=e.strip()
    if not e: return None
    if '[' in e or ']' in e: return None       # markers/data
    if '"' in e: return None
    if '/' in e: return None                    # any slash => desc continuation
    if e.endswith(('.','!','?',':',';')): return None
    if ',' in e: return None
    if '\n' in e: return None
    w=e.split()
    if len(w)>5: return None
    # at least starts uppercase letter (proper item name)
    if not e[0].isalpha(): return None
    return e

kw = re.compile(r'(potion|herb|antidote|elixir|salve|balm|tonic|medicine|cure|'
                r'stone|gem|crystal|jewel|ore|ingot|shard|fragment|powder|dust|'
                r'chip|hide|fang|claw|scale|horn|wing|feather|bone|'
                r'medal|coin|token|seal|emblem|badge|'
                r'key|pass|ticket|scroll|note|letter|map|tome|'
                r'water|oil|wine|bread|ration|meat|fruit|'
                r'ash|wood|cloth|silk|thread|rope|'
                r'ring|amulet|charm|talisman|pendant|necklace|bracelet|'
                r'root|seed|flower|leaf|mushroom|soul|spirit|essence|blood|tear|'
                r'bell|mirror|lamp|candle|torch|orb|sphere|wand|rod|staff|book|spellbook)', re.I)

seen=set()
out=[]
for f in files:
    try: d=json.load(open(f,encoding='utf-8'))
    except: continue
    if not isinstance(d,list): continue
    for rec in d:
        if not isinstance(rec,dict): continue
        res=str(rec.get('resource'))
        if res=='34': continue          # owned by other shards
        if res=='48': continue          # shop names not items
        e=name_like(rec.get('english'))
        if e is None: continue
        if len(e)<=12: continue
        msg=rec.get('message',rec.get('msg_index','?'))
        key=(res,e)
        if key in seen: continue
        seen.add(key)
        out.append((os.path.basename(f),res,msg,e,len(e),bool(kw.search(e)),rec.get('japanese','')))

out.sort(key=lambda x:(not x[5],x[1],-x[4]))
with open('build/scan4b_out.txt','w',encoding='utf-8') as w:
    w.write('=== SCOPED (item keyword) ===\n')
    for f,res,m,e,n,s,jp in out:
        if s: w.write('%-32s R%-5s m%-6s %2d  %s\n'%(f,res,m,n,e))
    w.write('\n=== UNSCOPED name-like >12 ===\n')
    for f,res,m,e,n,s,jp in out:
        if not s: w.write('%-32s R%-5s m%-6s %2d  %s\n'%(f,res,m,n,e))
print('scoped',sum(1 for x in out if x[5]),'unscoped',sum(1 for x in out if not x[5]))
