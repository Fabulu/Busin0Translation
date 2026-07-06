#!/usr/bin/env python3
import struct, sys, os
from collections import Counter
import zstandard as zstd
sys.stdout.reconfigure(encoding='utf-8')
SNAPS="C:/Users/Fabian Trunz/OneDrive - Berner Fachhochschule/Dokumente/PCSX2/snaps"
def parse_tex0(val):
    return {'tbp0':val&0x3FFF,'tbw':(val>>14)&0x3F,'psm':(val>>20)&0x3F,
            'tw':1<<((val>>26)&0xF),'th':1<<((val>>30)&0xF)}
def parse(path):
    dctx=zstd.ZstdDecompressor()
    data=dctx.decompress(open(path,'rb').read(),max_output_size=512*1024*1024)
    hts=struct.unpack_from("<I",data,4)[0]; sv,ss=struct.unpack_from("<II",data,8)
    ds=8+hts; pos=ds+ss+0x2000
    cur_tex0={1:None,2:None}; cur_xyoff={1:(0,0),2:(0,0)}
    prim_type=6;tme=0;prim_ctx=1;vsync=0; draws=[]
    def handle_ad(plo,ra):
        nonlocal prim_type,tme,prim_ctx
        if ra in(0x06,0x07): cur_tex0[1 if ra==0x06 else 2]=parse_tex0(plo)
        elif ra==0x00: prim_type=plo&7;tme=(plo>>4)&1;prim_ctx=((plo>>9)&1)+1
        elif ra in(0x18,0x19): cur_xyoff[1 if ra==0x18 else 2]=(plo&0xFFFF,(plo>>32)&0xFFFF)
    while pos<len(data):
        tag=data[pos];pos+=1
        if tag==0:
            pos+=1;size=struct.unpack_from("<I",data,pos)[0];pos+=4
            gif=data[pos:pos+size];pos+=size;g=0
            while g+16<=len(gif):
                lo,hi=struct.unpack_from("<QQ",gif,g)
                nloop=lo&0x7FFF;pre=(lo>>46)&1;pdata=(lo>>47)&0x7FF
                flg=(lo>>58)&3;nreg=(lo>>60)&0xF or 16;g+=16
                rids=[(hi>>(r*4))&0xF for r in range(nreg)]
                if flg==2: g+=nloop*16;continue
                verts=[];uvs=[]
                if pre: prim_type=pdata&7;tme=(pdata>>4)&1;prim_ctx=((pdata>>9)&1)+1
                if flg==0:
                    for _ in range(nloop):
                        for rid in rids:
                            if g+16>len(gif):break
                            plo=struct.unpack_from("<Q",gif,g)[0];phi=struct.unpack_from("<Q",gif,g+8)[0]
                            if rid==0x0E: handle_ad(plo,phi&0xFF)
                            elif rid in(0x04,0x05): verts.append((plo&0xFFFF,(plo>>16)&0xFFFF))
                            elif rid==0x03: uvs.append((plo&0x3FFF,(plo>>16)&0x3FFF))
                            elif rid==0x00: prim_type=plo&7;tme=(plo>>4)&1;prim_ctx=((plo>>9)&1)+1
                            g+=16
                else:
                    total=nloop*nreg
                    for i in range(total):
                        if g+8>len(gif):break
                        rid=rids[i%nreg];rd=struct.unpack_from("<Q",gif,g)[0]
                        if rid==0x00: prim_type=rd&7;tme=(rd>>4)&1;prim_ctx=((rd>>9)&1)+1
                        elif rid in(0x04,0x05): verts.append((rd&0xFFFF,(rd>>16)&0xFFFF))
                        elif rid==0x03: uvs.append((rd&0x3FFF,(rd>>16)&0x3FFF))
                        g+=8
                    if total%2:g+=8
                t0=cur_tex0.get(prim_ctx) or cur_tex0[1]
                if verts and tme and t0:
                    draws.append({'vsync':vsync,'prim':prim_type,'tex0':dict(t0),
                                  'verts':verts,'uvs':uvs,'xyoff':cur_xyoff.get(prim_ctx,(0,0))})
        elif tag==1: pos+=1;vsync+=1
        elif tag==2: size=struct.unpack_from("<I",data,pos)[0];pos+=4+size
        elif tag==3: pos+=0x2000
        else: break
    return draws

draws=parse(os.path.join(SNAPS,"Busin 0 - Wizardry Alternative Neo_SLPM-65378_20260612061701.gs.zst"))
font=[d for d in draws if d['tex0']['tbp0']==0x3000 and d['tex0']['psm']==20 and d['tex0']['tbw']==16]
print(f"PSMT4 tbw=16 font draws: {len(font)}")
vs=Counter(d['vsync'] for d in font); print("per vsync:",dict(vs))
tv=max(vs,key=lambda k:vs[k])
sel=[d for d in font if d['vsync']==tv]
def rect(d):
    ox,oy=d['xyoff']
    xs=[(v[0]-ox)/16.0 for v in d['verts']]; ys=[(v[1]-oy)/16.0 for v in d['verts']]
    us=[u[0]/16.0 for u in d['uvs']]; vsv=[u[1]/16.0 for u in d['uvs']]
    return (min(xs),min(ys),max(xs),max(ys),min(us) if us else None,max(us) if us else None,
            min(vsv) if vsv else None,max(vsv) if vsv else None)
rs=[rect(d) for d in sel]
rs.sort(key=lambda r:(round(r[1]/8)*8,r[0]))
prev=None;prevline=None
for r in rs:
    x0,y0,x1,y1,u0,u1,v0,v1=r
    line=round(y0/8)*8
    if line!=prevline:
        print(f"\n--- line y~{y0:.1f} ---"); prev=None
    step=f" stepX={x0-prev:+6.2f}" if prev is not None else ""
    uv=f" U[{u0:.0f}-{u1:.0f}]V[{v0:.0f}-{v1:.0f}]" if u0 is not None else ""
    print(f"  x[{x0:6.1f}-{x1:6.1f}] w={x1-x0:4.1f} y[{y0:.0f}-{y1:.0f}]{uv}{step}")
    prev=x0;prevline=line
