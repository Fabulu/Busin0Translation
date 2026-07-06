import struct,sys,os,json
sys.stdout.reconfigure(encoding='utf-8')
# Load glyph map to decode v99 English groups
gm=None
for p in ['data/english_glyph_table.json','data/glyph_map_partial.json']:
    if os.path.isfile(p):
        try: gm=json.load(open(p,encoding='utf-8')); print("loaded",p); break
        except: pass
# Build idx->char from whatever structure
inv={}
if gm:
    for k,v in gm.items():
        try:
            if isinstance(v,int): inv[v]=k
            elif isinstance(v,str) and v.isdigit(): inv[int(v)]=k
        except: pass
def groups(d):
    o=struct.unpack_from("<I",d,0x18)[0]; s2=d[o:]
    g=[];cur=[]
    for i in range(0,len(s2)-1,2):
        w=(s2[i]<<8)|s2[i+1];cur.append(w)
        if w==0xFFFF:g.append(cur);cur=[]
    return g
v99=open('build/patched_type2/1197_type02.raw','rb').read()
gv=groups(v99)
# Decode using ASCII assumption: many indices look like ascii-ish. 0x34='4'? No.
# From g652 v99: 0024='D'? 0x24=36. Let's just map: seems idx = ascii? 0x45=E,0x44=D,0x41=A...
# 0x45=69='E', 0x44=68='D' YES it's ASCII! 0x24=36='$'? no. Try idx for letters: 0x41='A'. 
def dec(g):
    out=""
    for w in g:
        if w==0xFFFE: out+=" / "
        elif w==0xFFFF: out+="¶"
        elif 0xFFC0<=w<=0xFFCF: out+="[OPT%d]"%(w-0xFFC0)
        elif w==0: out+=" "
        elif 32<=w<127: out+=chr(w)
        else: out+="{%x}"%w
    return out
for i in [63,652,916]:
    print("g%d:"%i, dec(gv[i]))
