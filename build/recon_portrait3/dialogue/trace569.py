import sys
sys.stdout.reconfigure(encoding='utf-8')
TYPE2_WRAP_WIDTH=16
def _wrap_line(seg,max_chars):
    out=[]
    while len(seg)>max_chars:
        brk=seg.rfind(' ',0,max_chars+1)
        if brk<=0: brk=max_chars
        out.append(seg[:brk]); seg=seg[brk:].lstrip(' ')
    out.append(seg)
    return out
def wrap_type2_text(text,max_chars=TYPE2_WRAP_WIDTH):
    pages=[]
    for page in text.split(' // '):
        lines=[]
        for seg in page.split(' / '):
            lines.extend(_wrap_line(seg,max_chars))
        pages.append(' / '.join(lines))
    return ' // '.join(pages)

# msg 569 actual
t="No one was in / sight. Not a / sound, not even / the wind."
w=wrap_type2_text(t)
print("input lines (translator):")
for l in t.split(' / '): print(f"   [{len(l):2d}] {l!r}")
print("after wrap:")
for l in w.split(' / '): print(f"   [{len(l):2d}] {l!r}")
# emit
glyphs_desc=[]
for page_i,page in enumerate(w.split(' // ')):
    if page_i>0: glyphs_desc.append('||PAGE||')
    line_count=0
    for pi,part in enumerate(page.split(' / ')):
        if pi>0:
            line_count+=1
            if line_count>=3:
                glyphs_desc.append('--PGBRK--'); line_count=0
            else:
                glyphs_desc.append('/LF/')
        glyphs_desc.append(part)
print("emitted sequence:")
print("   "+' '.join(glyphs_desc))
