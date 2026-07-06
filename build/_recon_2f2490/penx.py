import sys,struct,zipfile
sys.stdout.reconfigure(encoding='utf-8')
z=zipfile.ZipFile(sys.argv[1])
ee=[z.read(n) for n in z.namelist() if 'eeMemory' in n][0]
def u8(a): return ee[a]
def s16(a): return struct.unpack('<h',ee[a:a+2])[0]
def u16(a): return struct.unpack('<H',ee[a:a+2])[0]
def u32(a): return struct.unpack('<I',ee[a:a+4])[0]
def be16(a): return struct.unpack('>H',ee[a:a+2])[0]

desc=0x1137AC0
glyph_tbl=u32(desc+0x08)
boxX=s16(desc+0x3c); boxY=s16(desc+0x3e)
print("glyph_tbl s0[8] =",hex(glyph_tbl),"boxX",boxX,"boxY",boxY)
# glyph stream ptr desc[0x04]
stream=u32(desc+0x04)
print("stream desc[0x04] =",hex(stream))
# decode first ~30 BE cells
import json
gt=json.load(open(r"data/english_glyph_table.json"))
# build gid->char
gid2ch={}
for k,v in gt.items():
    try: gid2ch[int(v)]=k
    except: pass
ADV=[u8(0x4C7564+i) for i in range(48)]
LS=[u8(0x4C7690+i) for i in range(48)]
# The glyph descriptor records: per drawn glyph, table at glyph_tbl + idx*12, field +0x8 = X, +0xa = Y
# But idx here is the GID. Reconstruct line1 penX accumulation.
# Read stream cells
print("\n=== stream cells (BE, gid=hi byte) ===")
cells=[]
for i in range(60):
    c=be16(stream+i*2)
    hi=c>>8
    cells.append((c,hi))
# print decoded
txt=""
for c,hi in cells:
    if c==0xFEFF or c==0xFFFE: txt+="|"
    elif hi==0: txt+="."
    else:
        ch=gid2ch.get(hi,"?"+hex(hi))
        txt+=ch if len(ch)==1 else "["+ch+"]"
print(repr(txt[:80]))

# Reconstruct penX for line1 using ADV/LS. align==0 => pen_0x1ce starts 0, boxX=0.
# Per glyph draw order in func: X = boxX + glyph[0x8] + (pen_0x1ce - LS[gid]); then pen_0x1ce += ADV[gid] (at 0x4C7554 after)
# glyph[0x8] is the glyph X bearing from the glyph table; approximate as 0 (we don't have per-gid table easily). Compute pen only.
print("\n=== line1 penX reconstruction (pen_0x1ce accumulation, boxX=0) ===")
pen=0
total=0
line=[]
for c,hi in cells:
    if c==0xFEFF or c==0xFFFE: break
    gid=hi
    if gid==0: continue
    ls=LS[gid] if gid<len(LS) else 0
    adv=ADV[gid] if gid<len(ADV) else 0
    drawX = boxX + (pen - ls)
    line.append((gid2ch.get(gid,'?'),drawX,pen,ls,adv))
    pen+=adv
    total+=adv
print("first glyph drawX =",line[0][1],"  last char drawX",line[-1][1])
print("line1 total advance =",total,"px")
for ch,dx,pn,ls,adv in line[:8]:
    print(f"  '{ch}' drawX={dx} pen={pn} ls={ls} adv={adv}")
