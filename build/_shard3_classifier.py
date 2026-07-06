import struct, json, os, re
from collections import Counter
BASE="C:/Programmieren/wizardrytranslation"
glyph_map={int(k):v for k,v in json.load(open(BASE+"/data/msg_glyph_map.json",encoding="utf-8")).items()}
for gid_str,info in json.load(open(BASE+"/data/type2_glyph_overrides.json",encoding="utf-8")).items():
    glyph_map[int(gid_str)]=info["t2"]

def decode_glyph(g):
    if g==0xFFFE: return " / "
    if g==0xFFD2: return " // "
    if 0<=g<=94: return chr(g+0x20)
    if g in glyph_map: return glyph_map[g]
    return f"[{g:04X}]"
def decode_message(glyphs):
    out=[]
    for g in glyphs:
        if g>=0xFB00 and g not in (0xFFFE,0xFFD2): continue
        out.append(decode_glyph(g))
    return "".join(out)

def classify_group(glyphs):
    text_glyphs=[g for g in glyphs if g<0xFB00 and g not in (0xFFFE,0xFFD2)]
    if not text_glyphs: return (False,"",0,0)
    mapped=[g for g in text_glyphs if g<=94 or g in glyph_map]
    coverage=len(mapped)/len(text_glyphs)
    decoded=decode_message(glyphs)
    clean=re.sub(r'\[[0-9A-Fa-f]{4}\]','',decoded)
    jpn=len(re.findall(r'[぀-ヿ一-鿿　-〿＀-￯]',clean))
    ascii_words=re.findall(r'[A-Za-z]{3,}',clean)
    unmapped=len(text_glyphs)-len(mapped)
    ph_ratio=unmapped/len(text_glyphs)
    unmapped_vals=[g for g in text_glyphs if not (g<=94 or g in glyph_map)]
    dom=Counter(unmapped_vals).most_common(1)[0][1]/len(unmapped_vals) if unmapped_vals else 0
    binary_fill=(ph_ratio>0.5) or (dom>0.4 and unmapped>20)
    rchars=[]
    for g in text_glyphs:
        if g<=94: ch=chr(g+0x20)
        elif g in glyph_map: ch=glyph_map[g]
        else: ch=None
        if ch is not None and len(ch)==1 and not ch.isspace() and ch not in '　・':
            rchars.append(ch)
        else: rchars.append('\x00')
    runs=[r for r in "".join(rchars).split('\x00') if len(r)>=4]
    longest=max((len(r) for r in runs), default=0)
    # Binary record-table signature: the LONGEST readable run is short (<=8)
    # and that same run repeats >=4 times (fixed-size struct, e.g. coordinate
    # tables -> the project's [DATA]/[LAYOUT] resources, R1057 family). Real
    # dialogue has at least one long varied sentence (>=9 readable chars).
    repeated_pattern=False
    if runs:
        rc=Counter(runs)
        top_run,top_n=rc.most_common(1)[0]
        if len(top_run)<=8 and top_n>=4 and top_n>=len(runs)*0.5:
            repeated_pattern=True
        long_runs=[r for r in runs if len(r)==longest]
        if longest<=8 and rc[long_runs[0]]>=4:
            repeated_pattern=True
    is_dialogue=False
    if coverage>=0.55 and not binary_fill and not repeated_pattern:
        distinct_long=len({r for r in runs if len(r)>=5})
        if longest>=9 and (jpn>=2 or len(ascii_words)>=1 or re.search(r'[゠-ヿ]{3,}',clean)):
            is_dialogue=True
        elif longest>=6 and distinct_long>=4 and jpn>=4:
            is_dialogue=True
    return (is_dialogue, decoded, jpn, len(text_glyphs))

def get_groups(rid):
    p=BASE+f"/extracted/packdata_raw/{rid:04d}_type02.raw"
    if not os.path.exists(p): return None
    data=open(p,'rb').read()
    if len(data)<0x1C: return None
    sz=struct.unpack_from("<I",data,0x14)[0]; off=struct.unpack_from("<I",data,0x18)[0]
    if off==0 or off>=len(data) or sz<4: return []
    sec2=data[off:min(off+sz,len(data))]
    nw=len(sec2)//2
    words=[struct.unpack_from(">H",sec2,i*2)[0] for i in range(nw)]
    gs=[];start=0
    for i in range(nw):
        if words[i]==0xFFFF: gs.append(words[start:i]);start=i+1
    if start<nw: gs.append(words[start:nw])
    return gs

def dialogue_count(rid):
    gs=get_groups(rid)
    if gs is None: return None
    if gs==[]: return 0
    return sum(1 for g in gs if g and classify_group(g)[0])
