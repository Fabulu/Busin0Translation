import sys, os, struct, json, glob
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools')
from dialogue_classifier import build_dialogue_map
from patch_section1_offsets import group_choice_markers, inject_and_patch, HEADER_SIZE

# ---- glyph table (replicate build_v9 enc) ----
table = json.load(open('data/english_glyph_table.json', encoding='utf-8'))
table = {k: v for k, v in table.items()}
def enc(ch):
    if ch in table: return table[ch]
    if ch.lower() in table: return table[ch.lower()]
    return 31

TYPE2_WRAP_WIDTH=19
def _wrap_line(seg, max_chars):
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
        for seg in page.split(' / '): lines.extend(_wrap_line(seg,max_chars))
        pages.append(' / '.join(lines))
    return ' // '.join(pages)
BOX_CAPACITY=4; PAGINATE_MAX_LINES=20
def _line_count(w): return sum(len(p.split(' / ')) for p in w.split(' // '))
def _paginate(w,cap=BOX_CAPACITY):
    out=[]
    for page in w.split(' // '):
        lines=page.split(' / ')
        out.append(' // '.join(' / '.join(lines[i:i+cap]) for i in range(0,len(lines),cap)))
    return ' // '.join(out)

def load_choice(r):
    raw=open(f'extracted/packdata_raw/{r:04d}_type02.raw','rb').read()
    s2sz=struct.unpack_from('<I',raw,0x14)[0]; s2o=struct.unpack_from('<I',raw,0x18)[0]
    sec2=raw[s2o:s2o+s2sz]; n=len(sec2)//2
    words=[struct.unpack_from('>H',sec2,i*2)[0] for i in range(n)]
    ch=set();gi=0;start=0
    for i in range(n):
        if words[i]==0xFFFF:
            if group_choice_markers(words[start:i]): ch.add(gi)
            gi+=1;start=i+1
    return ch

R=1197
choice_groups=load_choice(R)
dialogue_groups=build_dialogue_map(R)
all_trans={}
for fn in glob.glob('data/type2_translated/batch_*.json'):
    for e in json.load(open(fn,encoding='utf-8')):
        if e.get('resource')==R and 'msg_index' in e and e.get('english') and not any(ord(c)>127 for c in e['english']):
            if e['english'].startswith(('[DATA]','[LAYOUT]','[BINARY]','[MAP]','[SYSTEM]','[GLYPH','[DEBUG]')): continue
            all_trans[e.get('msg_index',-1)]=e['english']

# replicate Step-4 encode
encoded={}
for mi,en_text in all_trans.items():
    if mi not in choice_groups:
        en_text=wrap_type2_text(en_text)
        if (mi in dialogue_groups and '\n' not in en_text and _line_count(en_text)<=PAGINATE_MAX_LINES):
            en_text=_paginate(en_text)
    glyphs=[]
    for pi,page in enumerate(en_text.split(' // ')):
        if pi>0: glyphs.append(0xFFD2)
        for li,part in enumerate(page.split(' / ')):
            if li>0: glyphs.append(0xFFFE)
            for ch in part: glyphs.append(enc(ch))
    encoded[mi]=glyphs

os.makedirs('build/recon_rt/phase4/out',exist_ok=True)
res=inject_and_patch(R,encoded,'extracted/packdata_raw','build/recon_rt/phase4/out')
print('inject result:',res[0],res[1])

# diff choice markers pristine vs injected
def parse_groups(raw):
    s2sz=struct.unpack_from('<I',raw,0x14)[0]; s2o=struct.unpack_from('<I',raw,0x18)[0]
    sec2=raw[s2o:s2o+s2sz]; n=len(sec2)//2
    words=[struct.unpack_from('>H',sec2,i*2)[0] for i in range(n)]
    groups=[];cur=[]
    for w in words:
        if w==0xFFFF: groups.append(cur);cur=[]
        else: cur.append(w)
    return groups

pri=open(f'extracted/packdata_raw/{R:04d}_type02.raw','rb').read()
inj=open(f'build/recon_rt/phase4/out/{R:04d}_type02.raw','rb').read()
pg=parse_groups(pri); ig=parse_groups(inj)
print('group count pristine=%d injected=%d %s'%(len(pg),len(ig),'OK' if len(pg)==len(ig) else '*** MISMATCH ***'))

# total choice markers across whole resource
def all_markers(groups):
    out=[]
    for gi,g in enumerate(groups):
        m=group_choice_markers(g)
        if m: out.append((gi,tuple(m)))
    return out
pm=all_markers(pg); im=all_markers(ig)
print('pristine choice markers:',pm)
print('injected choice markers:',im)
print('MARKERS IDENTICAL:', pm==im)

print('\n=== PAGINATION AUDIT ===')
print('choice_groups:', sorted(choice_groups))
print('dialogue_groups count:', len(dialogue_groups))
# did any group get a 0xFFD2 (page break) inserted that pristine did NOT have?
def count_ffd2(groups):
    return {gi:g.count(0xFFD2) for gi,g in enumerate(groups) if g.count(0xFFD2)>0}
p_ffd2=count_ffd2(pg); i_ffd2=count_ffd2(ig)
print('pristine groups WITH 0xFFD2:', p_ffd2)
print('injected groups WITH 0xFFD2 (sample):', dict(list(sorted(i_ffd2.items()))[:20]), '... total', len(i_ffd2))
# Of the injected 0xFFD2 groups, are ANY also choice groups? (the danger)
danger = set(i_ffd2) & choice_groups
print('CHOICE groups that received a 0xFFD2 (DANGER):', sorted(danger))
# For each choice group, dump pristine vs injected glyph stream around markers
for gi in sorted(choice_groups):
    pgl=pg[gi]; igl=ig[gi]
    print(f'\n--- choice g{gi}: pristine len {len(pgl)} / injected len {len(igl)} ---')
    print('  pristine ctrl words:', [hex(w) for w in pgl if w>=0xFB00])
    print('  injected ctrl words:', [hex(w) for w in igl if w>=0xFB00])
