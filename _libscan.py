import json,os,struct,glob
m=json.load(open('data/msg_glyph_map.json',encoding='utf-8'))
gid2c={int(k):v for k,v in m.items()}
rev={}
for k,v in m.items(): rev.setdefault(v,[]).append(int(k))

def seqs(s):
    # produce list of possible BE-u16 byte patterns for string s (cartesian small)
    opts=[rev.get(c,[]) for c in s]
    if any(not o for o in opts): return []
    res=[b'']
    for o in opts:
        nres=[]
        for prefix in res:
            for g in o:
                nres.append(prefix+struct.pack('>H',g))
        res=nres
    return res

targets={
 'LIBRARY(title)':'ライブラリー',
 'ITEMCOMPENDIUM(sub)':'アイテム図鑑',
}
patterns={name:seqs(s) for name,s in targets.items()}
d='extracted/packdata_resources'
files=sorted(glob.glob(d+'/*.bin'))
print('scanning',len(files),'files')
hits={}
for f in files:
    data=open(f,'rb').read()
    for name,pats in patterns.items():
        for p in pats:
            idx=data.find(p)
            if idx>=0:
                hits.setdefault(name,[]).append((os.path.basename(f),idx,len(data)))
                break
for name,h in hits.items():
    print('===',name,'===')
    for fn,idx,ln in h: print(f'  {fn} @0x{idx:X} (filelen {ln})')
