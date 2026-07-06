import sys, os, glob
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, "build/recon_v86/gs-vram-atlas")
import gs_atlas as G

SNAPS = "C:/Users/Fabian Trunz/OneDrive - Berner Fachhochschule/Dokumente/PCSX2/snaps"

def glyph_char(u, v):
    # u,v in texel units (UV register is 12.4 fixed -> already divided?) 
    # parser stores uvs as (plo & 0x3FFF, (plo>>16)&0x3FFF) which is UV in 1/16 texel
    col = (u//16)//24
    row = (v//16)//24
    gid = row*42 + col
    ch = gid + 32
    if 32 <= ch < 127:
        return chr(ch)
    return '?'

files = sorted(glob.glob(os.path.join(SNAPS, "*.gs.zst")))
print(f"{len(files)} dumps")
hits = []
for f in files:
    try:
        vram, draws, transfers, frames = G.parse_dump(f)
    except Exception as e:
        print("ERR", os.path.basename(f), e); continue
    # collect R1188 draws: tbp0==0x3000, psm==0x14(T4)
    text = []
    for d in draws:
        t0 = d['tex0']
        if t0['tbp0']==0x3000 and t0['psm']==0x14 and len(d['uvs'])>=1 and len(d['verts'])>=1:
            u,v = d['uvs'][0][:2] if isinstance(d['uvs'][0], tuple) and d['uvs'][0][0]!='st' else (0,0)
            text.append(glyph_char(u,v))
    s = ''.join(text)
    if any(k in s for k in ('No','one','was','sight','wind','sound','heavy','fog','the')) and len(s)>10:
        # rough check
        low = s.lower()
        if 'no' in low and 'in' in low or 'wind' in low or 'sound' in low or 'sight' in low:
            hits.append((os.path.basename(f), len([d for d in draws if d['tex0']['tbp0']==0x3000 and d['tex0']['psm']==0x14]), s[:120]))
for h in hits:
    print("HIT", h[0], "n3000T4draws=", h[1])
    print("   ", repr(h[2]))
