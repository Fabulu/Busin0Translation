import struct, json, os, re, sys
sys.stdout.reconfigure(encoding="utf-8")
BASE="C:/Programmieren/wizardrytranslation"
RAW=os.path.join(BASE,"extracted/packdata_raw")
gm=json.load(open(os.path.join(BASE,"data/msg_glyph_map.json"),encoding="utf-8"))
glyph_map={int(k):v for k,v in gm.items()}
ov=json.load(open(os.path.join(BASE,"data/type2_glyph_overrides.json"),encoding="utf-8"))
for k,info in ov.items():
    glyph_map[int(k)]=info["t2"]

# translated set
translated=set()
import glob
for bp in glob.glob(os.path.join(BASE,"data/type2_translated/*.json")):
    if bp.endswith(".master"): continue
    try: b=json.load(open(bp,encoding="utf-8"))
    except: continue
    if isinstance(b,list):
        for e in b:
            if isinstance(e,dict) and 'resource' in e and 'msg_index' in e:
                translated.add((e['resource'],e['msg_index']))

def decode_glyph(g):
    if g==0xFFFE: return " / "
    if g==0xFFD2: return " // "
    if 0<=g<=94: return chr(g+0x20)
    if g in glyph_map: return glyph_map[g]
    return f"[0x{g:04X}]"

def decode_message(glyphs):
    parts=[]
    for g in glyphs:
        if g>=0xFB00: continue
        parts.append(decode_glyph(g))
    return "".join(parts)

JP=re.compile(r"[぀-ゟ一-鿿　-〿]")
KATA=re.compile(r"[゠-ヿ]{2,}")
HEX=re.compile(r"\[0x[0-9A-Fa-f]{4}\]")

def is_dialogue_group(group):
    # relaxed: catch sparse dialogue (1-3 short messages)
    text=[g for g in group if g<0xFB00 and g not in (0xFFFE,0xFFD2)]
    if len(text)<3: return False,None
    mapped=sum(1 for g in text if g<=94 or g in glyph_map)
    if mapped<3: return False,None
    cov=mapped/len(text)
    if cov<0.45: return False,None
    decoded=decode_message(group)
    clean=HEX.sub("",decoded).replace(" / ","").replace(" // ","")
    realchars=re.sub(r"[\s`@]","",clean)
    if len(realchars)<3: return False,None
    hexn=len(HEX.findall(decoded))
    if hexn>len(realchars): return False,None
    # must contain hiragana/kanji OR a katakana word (>=2)
    has_jp=bool(JP.search(clean))
    has_kata=bool(KATA.search(clean))
    if not (has_jp or has_kata): return False,None
    # require a consecutive run of >=3 mapped non-space glyphs
    run=0;maxrun=0
    for g in text:
        m=(g<=94 or g in glyph_map); sp=(g<=1)
        if m and not sp: run+=1; maxrun=max(maxrun,run)
        else: run=0
    if maxrun<3: return False,None
    return True,decoded

def scan(rid):
    p=os.path.join(RAW,f"{rid:04d}_type02.raw")
    if not os.path.exists(p): return None
    d=open(p,"rb").read()
    if len(d)<0x1C: return {"id":rid,"kind":"undecodable","cnt":0,"samples":[],"note":"file<0x1C"}
    s2sz=struct.unpack_from("<I",d,0x14)[0]
    s2off=struct.unpack_from("<I",d,0x18)[0]
    if s2off==0 or s2off>=len(d) or s2sz<4:
        return {"id":rid,"kind":"binary","cnt":0,"samples":[],"note":f"no sec2 (off={s2off},sz={s2sz})"}
    end=min(s2off+s2sz,len(d))
    sec=d[s2off:end]
    nw=len(sec)//2
    words=struct.unpack(f">{nw}H",sec[:nw*2])
    groups=[];start=0
    for i in range(nw):
        if words[i]==0xFFFF:
            groups.append(words[start:i]); start=i+1
    if start<nw: groups.append(words[start:nw])
    total_groups=len(groups)
    dlg=0; samples=[]; untrans_dlg=0
    for mi,g in enumerate(groups):
        if not g: continue
        ok,dec=is_dialogue_group(g)
        if ok:
            dlg+=1
            if (rid,mi) not in translated:
                untrans_dlg+=1
                if len(samples)<3:
                    samples.append((mi,dec))
    if dlg==0:
        kind="binary"
    elif total_groups>0 and dlg/max(1,total_groups)>=0.5 and dlg>=3:
        kind="dialogue"
    else:
        kind="mixed"
    return {"id":rid,"kind":kind,"cnt":untrans_dlg,"total_dlg":dlg,"total_groups":total_groups,"samples":samples,"note":""}

# untranslated ids in range
ids=set()
for bp in glob.glob(os.path.join(BASE,"data/type2_translated/*.json")):
    if bp.endswith(".master"): continue
    try: b=json.load(open(bp,encoding="utf-8"))
    except: continue
    if isinstance(b,list):
        for e in b:
            if isinstance(e,dict) and 'resource' in e: ids.add(e['resource'])
raw_ids=[]
for fn in os.listdir(RAW):
    if fn.endswith("_type02.raw"):
        raw_ids.append(int(fn.split("_")[0]))
mine=sorted(r for r in raw_ids if 1601<=r<=2653 and r not in ids)

results=[]
for rid in mine:
    r=scan(rid)
    if r: results.append(r)

# write UTF-8 detail file with JP samples
with open(os.path.join(BASE,"build/_shard4_samples.txt"),"w",encoding="utf-8") as f:
    for r in results:
        f.write(f"R{r['id']} kind={r['kind']} untrans_dlg={r['cnt']} total_dlg={r.get('total_dlg')} groups={r.get('total_groups')} {r.get('note','')}\n")
        for mi,dec in r["samples"]:
            f.write(f"   M{mi}: {dec[:160]}\n")
        f.write("\n")

# ASCII summary to stdout
nd=sum(1 for r in results if r['kind']=='dialogue')
nm=sum(1 for r in results if r['kind']=='mixed')
nb=sum(1 for r in results if r['kind']=='binary')
nu=sum(1 for r in results if r['kind']=='undecodable')
print(f"SCANNED {len(results)} untranslated in 1601-2653: dialogue={nd} mixed={nm} binary={nb} undecodable={nu}")
print("RESOURCES WITH DIALOGUE (id:kind:untrans_dlg_count):")
for r in results:
    if r['cnt']>0:
        print(f"  R{r['id']}:{r['kind']}:{r['cnt']} (total_dlg={r.get('total_dlg')},groups={r.get('total_groups')})")
# dump json for structured output building
json.dump(results,open(os.path.join(BASE,"build/_shard4_results.json"),"w"),ensure_ascii=True)
