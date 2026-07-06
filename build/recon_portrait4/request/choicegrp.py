import sys, struct, json
sys.stdout.reconfigure(encoding='utf-8')
def sec2(path):
    d=open(path,'rb').read(); s2=struct.unpack_from('<I',d,0x18)[0]; return d[s2:]
# The 0x06 opcode at 0x110E: 0006 0016 0002 ffffffff 00001378 -> 0x06 handler 0x2F37E0 (u16,u16,u32,u32)
# operands: 0x0016, 0x0002, 0xffffffff, 0x00001378. The last u32 0x1378 looks like a sec2 group offset.
# Let's decode the choice group at the DISPLAY referenced near the menu. 
# Actually decode FFC0/FFC1 choice groups: from earlier scan R1197 choice word-indices.
# CUR choices at word idx: 3646/3651, 24929/24947, 26034/26044, 27828/27843, 28955/28971, 32162/32178, 38241/38255, 39067/39075
# JP choices: 2498/2503, 19398/19406, 20376/20385, 21424/21432, 22126/22135, 24388/24397, 28999/29006, 29412/29421
gm=json.load(open('data/msg_glyph_map.json',encoding='utf-8')) if __import__('os').path.exists('data/msg_glyph_map.json') else {}
rev={}
for k,v in gm.items():
    try: rev[int(k)]=v
    except:
        try: rev[int(v)]=k
        except: pass
def render(words):
    s=''
    for w in words:
        if w==0: s+='·'
        elif 0xFFC0<=w<=0xFFCF: s+='[C%d]'%(w-0xFFC0)
        elif w==0xFFFE: s+='/'
        elif w==0xFFFF: s+='|END|'
        elif w==0xFFD2: s+='//'
        elif w in rev: s+=rev[w]
        elif w>=0xFB00: s+='[%04X]'%w
        else: s+='{%d}'%w
    return s
def words(path):
    s2=sec2(path); return [struct.unpack_from('>H',s2,i)[0] for i in range(0,len(s2)-1,2)]
jw=words('extracted/packdata_raw/1197_type02.raw')
cw=words('build/packdata_resources/1197_type02.raw')
def around(w,idx,back=40,fwd=40):
    lo=max(0,idx-back); hi=min(len(w),idx+fwd)
    return render(w[lo:hi])
print("=== JP choice groups (first marker idxs) ===")
for ci in (2498,19398,20376,21424,22126,24388,28999,29412):
    print(f"  @w{ci}: ...{around(jw,ci)}...")
print("\n=== CUR choice groups ===")
for ci in (3646,24929,26034,27828,28955,32162,38241,39067):
    print(f"  @w{ci}: ...{around(cw,ci)}...")
