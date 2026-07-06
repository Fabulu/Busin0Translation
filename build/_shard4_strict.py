import struct,json,os,re,sys
sys.stdout.reconfigure(encoding="utf-8")
BASE="C:/Programmieren/wizardrytranslation"
RAW=os.path.join(BASE,"extracted/packdata_raw")
gm=json.load(open(os.path.join(BASE,"data/msg_glyph_map.json"),encoding="utf-8"))
glyph_map={int(k):v for k,v in gm.items()}
ov=json.load(open(os.path.join(BASE,"data/type2_glyph_overrides.json"),encoding="utf-8"))
for k,info in ov.items(): glyph_map[int(k)]=info["t2"]
def dg(g):
    if g==0xFFFE: return " / "
    if g==0xFFD2: return " // "
    if 0<=g<=94: return chr(g+0x20)
    if g in glyph_map: return glyph_map[g]
    return None  # unmapped
def groups_of(rid):
    p=os.path.join(RAW,f"{rid:04d}_type02.raw")
    if not os.path.exists(p): return None
    d=open(p,"rb").read()
    if len(d)<0x1C: return None
    s2sz=struct.unpack_from("<I",d,0x14)[0]; s2off=struct.unpack_from("<I",d,0x18)[0]
    if s2off==0 or s2off>=len(d) or s2sz<4: return None
    sec=d[s2off:min(s2off+s2sz,len(d))]
    nw=len(sec)//2; words=struct.unpack(f">{nw}H",sec[:nw*2])
    g=[];s=0
    for i in range(nw):
        if words[i]==0xFFFF: g.append(words[s:i]);s=i+1
    if s<nw: g.append(words[s:nw])
    return g
JPc=re.compile(r"[぀-ゟ゠-ヿ一-鿿]")
# untranslated ids in range
import glob
ids=set()
for bp in glob.glob(os.path.join(BASE,"data/type2_translated/*.json")):
    if bp.endswith(".master"): continue
    try: b=json.load(open(bp,encoding="utf-8"))
    except: continue
    if isinstance(b,list):
        for e in b:
            if isinstance(e,dict) and 'resource' in e: ids.add(e['resource'])
mine=sorted(int(fn.split("_")[0]) for fn in os.listdir(RAW) if fn.endswith("_type02.raw") and 1601<=int(fn.split("_")[0])<=2653 and int(fn.split("_")[0]) not in ids)
hits=0
for rid in mine:
    gs=groups_of(rid)
    if not gs: continue
    for mi,gr in enumerate(gs):
        toks=[dg(x) for x in gr if x<0xFB00]
        n=len(toks); 
        if n<6: continue
        mapped=sum(1 for t in toks if t is not None)
        if n==0 or mapped/n<0.85: continue   # STRICT: 85% mapped
        # longest consecutive run of mapped chars
        run=0;mx=0
        for t in toks:
            if t is not None: run+=1;mx=max(mx,run)
            else: run=0
        if mx<6: continue
        dec="".join(t for t in toks if t)
        # require some JP and a coherent feel: at least 6 mapped in a row with >=3 JP total
        if len(JPc.findall(dec))<3: continue
        hits+=1
        print(f"STRICT-HIT R{rid} M{mi} mapped={mapped}/{n} run={mx}: {dec[:120]}")
print(f"TOTAL STRICT HITS: {hits}")
