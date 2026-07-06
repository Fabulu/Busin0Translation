import sys, struct, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'build/recon_pag')
from spans import load
gm=json.load(open('data/msg_glyph_map.json',encoding='utf-8'))
res=int(sys.argv[1]); gis=[int(x) for x in sys.argv[2:]]
ok,instrs,sec1,groups,words=load(res)
for g in gis:
    gw=words[groups[g][0]:groups[g][1]]
    s=[]
    for w in gw:
        if w==0xFFFE: s.append(' / ')
        elif w==0xFFD2: s.append(' // ')
        elif w>=0xFB00: s.append('{%04X}'%w)
        else: s.append(gm.get(str(w),'?'))
    print("R%d g%d: %s"%(res,g,''.join(s)))
