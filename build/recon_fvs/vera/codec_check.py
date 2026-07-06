import sys, struct, json
sys.stdout.reconfigure(encoding='utf-8')
# R2654 codec per JSON: glyph_index = name_val - 95. katakana name_val 193-238 -> glyph 98-143.
# ASCII: name_val = ascii_gid+95 -> glyph = ascii_gid (0-94) = R2100 page-0 ASCII cell.
# For R1892, the name field stores SAME name_values (273=ヴ etc). So SAME codec applies.
# Vera katakana name_vals in R1892: 273(ヴ) 270(ェ) 93(ー) 231(ラ).
# Wait 93 < 95 -> glyph = 93-95 = -2?? The 'ー' long-vowel = name_val 93. 
# So codec glyph=name_val-95 gives 93->-2 which is wrong. Let me reconsider.
# Maybe codec is different. Check: katakana ア in R1892? Aoi = アオイ. 
KATA_BASE=193
# From sub7 raw earlier: アウローラ(Aurora) was 00c1 00c4? no. Let me recheck sub7 e1 raw: 0080 00b4...(that was romaji Aurora). 
# Pristine sub7 e1 アウローラ. Let me get its raw name_vals.
prist=open('extracted/packdata_raw/2654_type44.raw','rb').read()
def hdr(r): return [dict(zip(('sub','size','off','z'), struct.unpack_from('<4I', r, i*16))) for i in range(44)]
H=hdr(prist); h7=next(x for x in H if x['sub']==7)
off,size=h7['off'],h7['size']
cnt=struct.unpack_from('>H',prist,off)[0]
offs=[struct.unpack_from('>H',prist,off+4+i*4)[0] for i in range(cnt)]
for i in (1,2,7):
    st=off+offs[i]; en=off+(offs[i+1] if i+1<cnt else size)
    seg=prist[st:en]
    words=[struct.unpack_from('>H',seg,p)[0] for p in range(0,len(seg)-1,2)]
    print(f'sub7 e{i} raw name_vals:', [hex(w) for w in words if w not in (0xfffe,0xffff)])
# ア = first katakana. アウローラ first char ア
