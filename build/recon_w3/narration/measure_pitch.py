import struct, sys, os
import numpy as np
import zstandard as zstd
sys.stdout.reconfigure(encoding='utf-8')

SNAPS = "C:/Users/Fabian Trunz/OneDrive - Berner Fachhochschule/Dokumente/PCSX2/snaps"
TS = "20260612061701"  # narration dump
path = os.path.join(SNAPS, f"Busin 0 - Wizardry Alternative Neo_SLPM-65378_{TS}.gs.zst")

dctx = zstd.ZstdDecompressor()
data = dctx.decompress(open(path,'rb').read(), max_output_size=512*1024*1024)
hts = struct.unpack_from("<I", data, 4)[0]
sv, ss = struct.unpack_from("<II", data, 8)
ds = 8 + hts
print("state_version", sv, "ss", ss)
pos = ds + ss + 0x2000

# Collect all sprite (prim type 6) draws with TME=1, their tex0 tbp0, and screen coords
draws = []
cur_tex0 = {1:None,2:None}
cur_xyoff = {1:(0,0),2:(0,0)}
prim_type=6; tme=0; prim_ctx=1
vsync=0

def parse_tex0(val):
    return {'tbp0':val&0x3FFF,'tbw':(val>>14)&0x3F,'psm':(val>>20)&0x3F,
            'tw':1<<((val>>26)&0xF),'th':1<<((val>>30)&0xF)}

def handle_ad(plo, ra):
    global prim_type,tme,prim_ctx
    if ra in (0x06,0x07):
        cur_tex0[1 if ra==0x06 else 2]=parse_tex0(plo)
    elif ra==0x00:
        prim_type=plo&7; tme=(plo>>4)&1; prim_ctx=((plo>>9)&1)+1
    elif ra in (0x18,0x19):
        cur_xyoff[1 if ra==0x18 else 2]=(plo&0xFFFF,(plo>>32)&0xFFFF)

while pos < len(data):
    tag = data[pos]; pos+=1
    if tag==0:
        pos+=1
        size=struct.unpack_from("<I",data,pos)[0]; pos+=4
        gif=data[pos:pos+size]; pos+=size
        g=0
        while g+16<=len(gif):
            lo,hi=struct.unpack_from("<QQ",gif,g)
            nloop=lo&0x7FFF; pre=(lo>>46)&1; pdata=(lo>>47)&0x7FF
            flg=(lo>>58)&3; nreg=(lo>>60)&0xF or 16
            g+=16
            rids=[(hi>>(r*4))&0xF for r in range(nreg)]
            if flg==2:
                g+=nloop*16; continue
            verts=[]; uvs=[]
            if pre:
                prim_type=pdata&7; tme=(pdata>>4)&1; prim_ctx=((pdata>>9)&1)+1
            if flg==0:
                for _ in range(nloop):
                    for rid in rids:
                        if g+16>len(gif): break
                        plo=struct.unpack_from("<Q",gif,g)[0]
                        phi=struct.unpack_from("<Q",gif,g+8)[0]
                        if rid==0x0E: handle_ad(plo, phi&0xFF)
                        elif rid in (0x04,0x05): verts.append((plo&0xFFFF,(plo>>16)&0xFFFF))
                        elif rid==0x03: uvs.append((plo&0x3FFF,(plo>>16)&0x3FFF))
                        elif rid==0x00:
                            prim_type=plo&7; tme=(plo>>4)&1; prim_ctx=((plo>>9)&1)+1
                        g+=16
            else:
                total=nloop*nreg
                for i in range(total):
                    if g+8>len(gif): break
                    rid=rids[i%nreg]; rd=struct.unpack_from("<Q",gif,g)[0]
                    if rid==0x00:
                        prim_type=rd&7; tme=(rd>>4)&1; prim_ctx=((rd>>9)&1)+1
                    elif rid in (0x04,0x05): verts.append((rd&0xFFFF,(rd>>16)&0xFFFF))
                    elif rid==0x03: uvs.append((rd&0x3FFF,(rd>>16)&0x3FFF))
                    g+=8
                if total%2: g+=8
            t0=cur_tex0.get(prim_ctx) or cur_tex0[1]
            if verts and tme and t0 and prim_type==6:
                ox,oy=cur_xyoff.get(prim_ctx,(0,0))
                draws.append({'vsync':vsync,'tbp0':t0['tbp0'],'psm':t0['psm'],
                              'verts':verts,'uvs':uvs,'ox':ox,'oy':oy})
    elif tag==1: pos+=1; vsync+=1
    elif tag==2:
        size=struct.unpack_from("<I",data,pos)[0]; pos+=4+size
    elif tag==3: pos+=0x2000
    else: break

print("total sprite draws:", len(draws))
# group by tbp0
from collections import Counter
c=Counter((d['tbp0'],d['psm']) for d in draws)
for (tbp,psm),n in c.most_common(20):
    print(f"  tbp0=0x{tbp:04X} psm=0x{psm:02X} count={n}")

print("\n=== R1188 font draws (tbp0=0x3000 psm=0x14) ===")
font = [d for d in draws if d['tbp0']==0x3000 and d['psm']==0x14]
# group by vsync (frame)
from collections import defaultdict
byv=defaultdict(list)
for d in font: byv[d['vsync']].append(d)
for v in sorted(byv):
    ds=byv[v]
    print(f"\n--- vsync {v}: {len(ds)} glyph sprites ---")
    rows=[]
    for d in ds:
        xs=[(vv[0]-d['ox'])/16.0 for vv in d['verts']]
        ys=[(vv[1]-d['oy'])/16.0 for vv in d['verts']]
        us=[u[0]/16.0 for u in d['uvs']]
        vs=[u[1]/16.0 for u in d['uvs']]
        rows.append((min(xs),min(ys),max(xs),max(ys),min(us) if us else 0,min(vs) if vs else 0,max(us) if us else 0,max(vs) if vs else 0))
    rows.sort(key=lambda r:(round(r[1]),r[0]))
    for r in rows:
        print(f"  x0={r[0]:6.1f} y0={r[1]:6.1f} x1={r[2]:6.1f} y1={r[3]:6.1f}  w={r[2]-r[0]:4.1f} h={r[3]-r[1]:4.1f}  u0={r[4]:5.1f} v0={r[5]:5.1f} u1={r[6]:5.1f} v1={r[7]:5.1f}")
