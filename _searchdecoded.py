import json,os,glob
needles=['ライブラリー','アイテム図鑑','人物名鑑','用語辞典','冒険の手引き','書物リスト','早送り']
def scan(path):
    try: txt=open(path,encoding='utf-8',errors='replace').read()
    except: return
    for n in needles:
        if n in txt:
            # report ascii-safe
            idx=txt.find(n)
            print('HIT %-40s needle#%d @char%d'%(os.path.basename(path),needles.index(n),idx))
files=[]
for pat in ['data/*.json','data/*.txt','data/**/*.json','build/*.json','build/*.txt','*.txt']:
    files+=glob.glob(pat,recursive=True)
seen=set()
for f in files:
    if f in seen: continue
    seen.add(f); scan(f)
