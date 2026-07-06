import struct, json, os, re
BASE="C:/Programmieren/wizardrytranslation"
RAW_DIR=os.path.join(BASE,"extracted/packdata_raw")
glyph_map={int(k):v for k,v in json.load(open(BASE+"/data/msg_glyph_map.json",encoding="utf-8")).items()}
for gid_str,info in json.load(open(BASE+"/data/type2_glyph_overrides.json",encoding="utf-8")).items():
    glyph_map[int(gid_str)]=info["t2"]

def decode_glyph(g):
    if g==0xFFFE: return " / "
    if g==0xFFD2: return " // "
    if 0<=g<=94: return chr(g+0x20)
    if g in glyph_map: return glyph_map[g]
    return f"[{g:04X}]"

# Validate against a KNOWN translated resource: R1196 (from batch_01)
for rid in (1196,1063,1079):
    path=os.path.join(RAW_DIR,f"{rid:04d}_type02.raw")
    data=open(path,'rb').read()
    sec2_size=struct.unpack_from("<I",data,0x14)[0]
    sec2_off=struct.unpack_from("<I",data,0x18)[0]
    print(f"R{rid}: len={len(data)} sec2_size={sec2_size} sec2_off={sec2_off}")
    # also dump header words
    hdr=struct.unpack_from("<7I",data,0)
    print("  header u32[0..6]:", [hex(x) for x in hdr])
    sec2=data[sec2_off:min(sec2_off+sec2_size,len(data))]
    nw=len(sec2)//2
    words=[struct.unpack_from(">H",sec2,i*2)[0] for i in range(nw)]
    nffff=sum(1 for w in words if w==0xFFFF)
    print(f"  sec2 words={nw} FFFF count={nffff}")
    # decode first 2 groups
    groups=[];start=0
    for i in range(nw):
        if words[i]==0xFFFF: groups.append(words[start:i]);start=i+1
    out=[]
    for gi,grp in enumerate(groups[:3]):
        dec="".join(decode_glyph(g) for g in grp if g<0xFB00 or g in (0xFFFE,0xFFD2))
        out.append(f"  [g{gi}] {dec[:120]}")
    open(BASE+f"/build/_shard3_valid_{rid}.txt","w",encoding="utf-8").write("\n".join(out))
    # ascii preview
    for line in out:
        print("".join(c if 32<=ord(c)<127 else '.' for c in line)[:130])
    print()
