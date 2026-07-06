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
    return f"[{g:04X}]"
JP=re.compile(r"[぀-ゟ一-鿿]")
def groups_of(rid):
    p=os.path.join(RAW,f"{rid:04d}_type02.raw")
    d=open(p,"rb").read()
    s2sz=struct.unpack_from("<I",d,0x14)[0]; s2off=struct.unpack_from("<I",d,0x18)[0]
    sec=d[s2off:min(s2off+s2sz,len(d))]
    nw=len(sec)//2; words=struct.unpack(f">{nw}H",sec[:nw*2])
    g=[];s=0
    for i in range(nw):
        if words[i]==0xFFFF: g.append(words[s:i]);s=i+1
    if s<nw: g.append(words[s:nw])
    return g
# For a few "binary" resources, find the group with the MOST hiragana/kanji and print it
for rid in [int(x) for x in sys.argv[1:]]:
    gs=groups_of(rid)
    best=[]
    for mi,gr in enumerate(gs):
        dec="".join(dg(x) for x in gr if x<0xFB00)
        jpn=len(JP.findall(dec))
        if jpn>=3:
            best.append((jpn,mi,dec))
    best.sort(reverse=True)
    print(f"=== R{rid}: groups={len(gs)} groups_with_3+JP={len(best)} ===")
    for jpn,mi,dec in best[:4]:
        print(f"  M{mi} jp={jpn}: {dec[:140]}")
