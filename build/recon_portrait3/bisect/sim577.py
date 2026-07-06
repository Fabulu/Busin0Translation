import sys, json, struct, importlib.util, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir('C:/programmieren/wizardrytranslation')

table=json.load(open('data/english_glyph_table.json',encoding='utf-8'))
def enc(ch):
    if ch in table: return table[ch]
    if ch.lower() in table: return table[ch.lower()]
    return 31

# wrap helpers (new build_v9)
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
                if line_count>=3:
                    glyphs.append(0xFFD2); line_count=0
                else:
                    glyphs.append(0xFFFE)
            for ch in part: glyphs.append(enc(ch))
    return glyphs

src='Hey friend, hehe -- / you know where / God hides, right?'
print("ENC NOWRAP:", [hex(x) for x in encode(src,False)])
print()
print("ENC WRAP16:", [hex(x) for x in encode(src,True)])
