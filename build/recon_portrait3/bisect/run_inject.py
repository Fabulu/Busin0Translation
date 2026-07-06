import sys, json, struct, importlib.util, os, glob
sys.stdout.reconfigure(encoding='utf-8')
os.chdir('C:/programmieren/wizardrytranslation')
sys.path.insert(0,'tools')

table=json.load(open('data/english_glyph_table.json',encoding='utf-8'))
def enc(ch):
    if ch in table: return table[ch]
    if ch.lower() in table: return table[ch.lower()]
    return 31
def _wrap_line(seg,max_chars):
    out=[]
    while len(seg)>max_chars:
        brk=seg.rfind(' ',0,max_chars+1)
        if brk<=0: brk=max_chars
        out.append(seg[:brk]); seg=seg[brk:].lstrip(' ')
    out.append(seg); return out
def wrap_type2_text(text,max_chars=16):
    pages=[]
    for page in text.split(' // '):
        lines=[]
        for seg in page.split(' / '):
            lines.extend(_wrap_line(seg,max_chars))
        pages.append(' / '.join(lines))
    return ' // '.join(pages)
def encode(en_text, do_wrap):
    if do_wrap: en_text=wrap_type2_text(en_text)
    glyphs=[]
    for page_i,page in enumerate(en_text.split(' // ')):
        if page_i>0: glyphs.append(0xFFD2)
        line_count=0
        for pi,part in enumerate(page.split(' / ')):
            if pi>0:
                line_count+=1
                if line_count>=3: glyphs.append(0xFFD2); line_count=0
                else: glyphs.append(0xFFFE)
            for ch in part: glyphs.append(enc(ch))
    return glyphs

all_trans={}
for fn in sorted(glob.glob('data/type2_translated/batch_*.json')):
    try:
        d=json.load(open(fn,encoding='utf-8'))
        for e in d:
            r=e['resource']; mi=e['msg_index']; en=e.get('english','')
            if r==1196 and en and not any(ord(c)>127 for c in en):
                all_trans[mi]=en
    except Exception: pass

mode=sys.argv[1]; modpath=sys.argv[2]
do_wrap=(mode=='new')
encoded={mi:encode(t,do_wrap) for mi,t in all_trans.items()}

spec=importlib.util.spec_from_file_location('inj_'+mode,modpath)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
outdir='build/recon_portrait3/bisect/out_'+mode
os.makedirs(outdir,exist_ok=True)
res=m.inject_and_patch(1196, encoded,'extracted/packdata_raw',outdir)
print("inject result:",res)

raw=open(outdir+'/1196_type02.raw','rb').read()
sec2_size=struct.unpack_from('<I',raw,0x14)[0]; sec2_off=struct.unpack_from('<I',raw,0x18)[0]
sec2=raw[sec2_off:sec2_off+sec2_size]
words=[struct.unpack_from('>H',sec2,i*2)[0] for i in range(len(sec2)//2)]
groups=[];cur=[]
for w in words:
    if w==0xFFFF: groups.append(cur);cur=[]
    else: cur.append(w)
if cur: groups.append(cur)
g=groups[577]
print("group577 (%d):"%len(g),[hex(x) for x in g])
