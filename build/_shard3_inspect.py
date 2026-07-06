import struct, json, os, re
from collections import Counter
BASE="C:/Programmieren/wizardrytranslation"
glyph_map={int(k):v for k,v in json.load(open(BASE+"/data/msg_glyph_map.json",encoding="utf-8")).items()}
for gid_str,info in json.load(open(BASE+"/data/type2_glyph_overrides.json",encoding="utf-8")).items():
    glyph_map[int(gid_str)]=info["t2"]

def get_groups(rid):
    data=open(BASE+f"/extracted/packdata_raw/{rid:04d}_type02.raw",'rb').read()
    sz=struct.unpack_from("<I",data,0x14)[0]; off=struct.unpack_from("<I",data,0x18)[0]
    sec2=data[off:min(off+sz,len(data))]
    nw=len(sec2)//2
    words=[struct.unpack_from(">H",sec2,i*2)[0] for i in range(nw)]
    groups=[];start=0
    for i in range(nw):
        if words[i]==0xFFFF: groups.append(words[start:i]);start=i+1
    if start<nw: groups.append(words[start:nw])
    return groups,words

for rid in (1063,1079,914,926,1055):
    groups,words=get_groups(rid)
    print(f"=== R{rid}: {len(groups)} groups, {len(words)} words ===")
    # stats per group
    for gi,grp in enumerate(groups[:2]):
        tg=[g for g in grp if g<0xFB00 and g not in (0xFFFE,0xFFD2)]
        mapped=[g for g in tg if g<=94 or g in glyph_map]
        unm=[g for g in tg if not(g<=94 or g in glyph_map)]
        c=Counter(g for g in tg)
        # what glyph values dominate?
        top=c.most_common(6)
        print(f"  g{gi}: total={len(tg)} mapped={len(mapped)} unmapped={len(unm)} cov={len(mapped)/max(1,len(tg)):.2f}")
        print(f"     top glyphs: {[(hex(v),n) for v,n in top]}")
        # decode just the mapped ones in sequence
        dec="".join(glyph_map.get(g, chr(g+0x20) if 0<=g<=94 else "") for g in tg)
        ascii_only="".join(c if 32<=ord(c)<127 else '.' for c in dec)
        print(f"     mapped-decode(ascii): {ascii_only[:100]}")
    print()
