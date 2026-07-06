import sys, struct, json, glob, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools'); sys.path.insert(0,'build')
import patch_section1_offsets as P
P._load_tables()
ENG=P._ENG_TABLE
ENG_REV=P._ENG_REV

def enc(ch):
    if ch in ENG: return ENG[ch]
    if ch.lower() in ENG: return ENG[ch.lower()]
    return 31

# replicate build_v9 wrap helpers
TYPE2_WRAP_WIDTH=16
def _wrap_line(seg,max_chars):
    out=[]
    while len(seg)>max_chars:
        brk=seg.rfind(' ',0,max_chars+1)
        if brk<=0: brk=max_chars
        out.append(seg[:brk]); seg=seg[brk:].lstrip(' ')
    out.append(seg); return out
def wrap_type2_text(text,max_chars=TYPE2_WRAP_WIDTH):
    pages=[]
    for page in text.split(' // '):
        lines=[]
        for seg in page.split(' / '):
            lines.extend(_wrap_line(seg,max_chars))
        pages.append(' / '.join(lines))
    return ' // '.join(pages)

src="Hey friend, hehe -- / you know where / God hides, right?"
print("SOURCE:",repr(src))
wrapped=wrap_type2_text(src)
print("WRAPPED:",repr(wrapped))
# encode like step4
glyphs=[]
for page_i,page in enumerate(wrapped.split(' // ')):
    if page_i>0: glyphs.append(0xFFD2)
    line_count=0
    for pi,part in enumerate(page.split(' / ')):
        if pi>0:
            line_count+=1
            if line_count>=3: glyphs.append(0xFFD2); line_count=0
            else: glyphs.append(0xFFFE)
        for ch in part: glyphs.append(enc(ch))
print("ENCODED glyphs:",' '.join('%04X'%g for g in glyphs))
# decode back
def show(w):
    o=[]
    for g in w:
        if g==0xFFFE: o.append('|LB|')
        elif g==0xFFD2: o.append('|PB|')
        elif g>=0xFB00: o.append('<%04X>'%g)
        elif g in ENG_REV: o.append(ENG_REV[g])
        else: o.append('?%d'%g)
    return ''.join(o)
print("DECODED:",show(glyphs))
# Check space glyph value
print("\nspace glyph =",ENG.get(' '),"  ',' =",ENG.get(','),"  '-' =",ENG.get('-'))
