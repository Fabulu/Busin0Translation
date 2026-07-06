import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'C:/programmieren/wizardrytranslation/build')
# Replicate the build's wrap + page-break logic without importing the whole module
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

texts={
 'R1196/577 Shady':"Hey friend, hehe -- / you know where / God hides, right?",
 'Narration sound':"No one was in sight. / Not a sound, not even / the wind.",
 'Narration man':"A man approached, / staggering on his feet.",
}
for name,t in texts.items():
    w=wrap_type2_text(t)
    print(f"=== {name} ===")
    print("  raw   :",repr(t))
    print("  wrapped:",repr(w))
    # now simulate glyph break emission
    breaks=[]
    for page_i,page in enumerate(w.split(' // ')):
        if page_i>0: breaks.append('FFD2(page//)')
        line_count=0
        for pi,part in enumerate(page.split(' / ')):
            if pi>0:
                line_count+=1
                if line_count>=3:
                    breaks.append(f'FFD2(auto3)<<{part!r}'); line_count=0
                else:
                    breaks.append(f'FFFE<<{part!r}')
    print("  break sequence:")
    for b in breaks: print("    ",b)
    # show the on-screen lines split at FFD2 (page) -> separate boxes
    print()
