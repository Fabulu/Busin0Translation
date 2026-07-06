#!/usr/bin/env python3
"""Shard 0 scoping scan: R680-R760 untranslated type-02 dialogue detection.
Less-aggressive: detect ANY natural-language run (>=3 consecutive mapped
kana/kanji glyphs, or ASCII words) even amid binary data.
Writes UTF-8 detail; prints only ASCII summary."""
import struct, json, os, io, sys, unicodedata

os.chdir("C:/programmieren/wizardrytranslation")
gmap = json.load(open("data/msg_glyph_map.json", encoding="utf-8"))

def cat_of(ch):
    o = ord(ch)
    if 0x20 <= o < 0x7f: return 'a'      # ascii
    if 0x3040 <= o <= 0x309f: return 'h'  # hira
    if 0x30a0 <= o <= 0x30ff: return 'k'  # kata
    if 0x4e00 <= o <= 0x9fff: return 'j'  # kanji
    if 0xff00 <= o <= 0xffef: return 'f'  # fullwidth
    return 'o'

UNTRANS = [680,681,683,684,685,686,687,688,689,691,693,694,695,697,698,699,
701,703,704,705,706,707,708,709,711,713,714,716,717,718,721,723,724,725,727,
729,730,731,732,733,734,735,737,738,739,745,749,751,752,753,754,755,756,759,760]

def count_seq_table(raw, start):
    # mirror build_full_english_v2 count_sequential_table heuristic loosely:
    # entries of 16 bytes where first u32 increments. We don't strictly need it;
    # we parse ALL FFFF groups across whole file to be thorough.
    return 0

def parse_all_ffff_groups(data):
    """Parse entire file as BE u16 words; split on 0xFFFF. Returns list of groups
    (each a list of u16) with their start word index."""
    nwords = len(data)//2
    groups=[]
    cur=[]; cur_start=0
    for i in range(nwords):
        w=(data[2*i]<<8)|data[2*i+1]
        if w==0xFFFF:
            if cur: groups.append((cur_start,cur))
            cur=[]; cur_start=i+1
        else:
            if not cur: cur_start=i
            cur.append(w)
    if cur: groups.append((cur_start,cur))
    return groups

def decode_group(grp):
    """Return (text_chars list, cats string, n_mapped, n_unmapped, n_control, fb_tags)."""
    chars=[]; cats=[]; mapped=0; unmapped=0; control=0; fb=0
    for g in grp:
        if g==0xFFFE:
            chars.append(' / '); cats.append('.')
        elif 0xFB00<=g<=0xFB0F:
            fb+=1; control+=1; chars.append('<FB%02X>'%(g&0xff)); cats.append('.')
        elif g>=0xFB00:
            control+=1; chars.append('<%04X>'%g); cats.append('.')
        else:
            s=str(g)
            if s in gmap and gmap[s]:
                ch=gmap[s]; chars.append(ch); cats.append(cat_of(ch[0])); mapped+=1
            else:
                chars.append('<%04X>'%g); cats.append('?'); unmapped+=1
    return chars,''.join(cats),mapped,unmapped,control,fb

def longest_lang_run(cats):
    """Longest run of language chars (a/h/k/j/f) treating ascii too."""
    best=0; cur=0; best_jp=0; cur_jp=0
    for c in cats:
        if c in 'ahkjf':
            cur+=1; best=max(best,cur)
        else:
            cur=0
        if c in 'hkjf':
            cur_jp+=1; best_jp=max(best_jp,cur_jp)
        else:
            cur_jp=0
    return best,best_jp

def romaji_gloss(chars):
    """Build a short ASCII gloss: kana->romaji-ish, kanji-> '#', ascii kept."""
    KATA={'ア':'a','イ':'i','ウ':'u','エ':'e','オ':'o','カ':'ka','キ':'ki','ク':'ku','ケ':'ke','コ':'ko',
    'サ':'sa','シ':'shi','ス':'su','セ':'se','ソ':'so','タ':'ta','チ':'chi','ツ':'tsu','テ':'te','ト':'to',
    'ナ':'na','ニ':'ni','ヌ':'nu','ネ':'ne','ノ':'no','ハ':'ha','ヒ':'hi','フ':'fu','ヘ':'he','ホ':'ho',
    'マ':'ma','ミ':'mi','ム':'mu','メ':'me','モ':'mo','ヤ':'ya','ユ':'yu','ヨ':'yo','ラ':'ra','リ':'ri',
    'ル':'ru','レ':'re','ロ':'ro','ワ':'wa','ヲ':'wo','ン':'n','ガ':'ga','ギ':'gi','グ':'gu','ゲ':'ge',
    'ゴ':'go','ザ':'za','ジ':'ji','ズ':'zu','ゼ':'ze','ゾ':'zo','ダ':'da','ヂ':'di','ヅ':'du','デ':'de',
    'ド':'do','バ':'ba','ビ':'bi','ブ':'bu','ベ':'be','ボ':'bo','パ':'pa','ピ':'pi','プ':'pu','ペ':'pe',
    'ポ':'po','ー':'-','ァ':'a','ィ':'i','ゥ':'u','ェ':'e','ォ':'o','ッ':'_','ャ':'ya','ュ':'yu','ョ':'yo'}
    out=[]
    for ch in chars:
        if ch==' / ': out.append('/')
        elif ch.startswith('<'): out.append('.')
        else:
            c=ch[0]; o=ord(c)
            if 0x20<=o<0x7f: out.append(c)
            elif c in KATA: out.append(KATA[c])
            else:
                # hira -> map by converting to kata range
                if 0x3040<=o<=0x309f:
                    kc=chr(o+0x60)
                    out.append(KATA.get(kc,'~'))
                elif 0x4e00<=o<=0x9fff: out.append('#')  # kanji placeholder
                else: out.append('~')
    g=''.join(out)
    return g[:80]

results={}
detail=io.open('build/_shard0_detail.txt','w',encoding='utf-8')
for rid in UNTRANS:
    path=f'extracted/packdata_raw/{rid:04d}_type02.raw'
    if not os.path.isfile(path):
        results[rid]={'kind':'undecodable','dialogue':0,'note':'file missing'}
        continue
    data=open(path,'rb').read()
    groups=parse_all_ffff_groups(data)
    dialogue_groups=[]
    total_fb=0
    samples=[]
    sample_cats=[]
    for gi,(st,grp) in enumerate(groups):
        if not grp: continue
        chars,cats,mapped,unmapped,control,fb=decode_group(grp)
        total_fb+=fb
        run,run_jp=longest_lang_run(cats)
        glen=len(grp)
        # Heuristic for a real dialogue/text message group:
        #  - contains a run of >=4 consecutive language glyphs (jp>=4 OR ascii word>=4)
        #  - mapped glyphs dominate the language portion
        is_dialogue=False
        if run_jp>=4:
            is_dialogue=True
        elif run>=5 and mapped>=5 and unmapped<=mapped:
            is_dialogue=True
        # also FB speaker tag + some mapped text strongly indicates dialogue
        if fb>=1 and (mapped>=3) and run>=3:
            is_dialogue=True
        if is_dialogue:
            dialogue_groups.append(gi)
            if len(samples)<4:
                samples.append(romaji_gloss(chars))
    ndlg=len(dialogue_groups)
    # classify resource
    if ndlg==0:
        kind='binary'
    else:
        # mixed if many groups but few dialogue; dialogue if most text groups are dialogue
        kind='mixed' if (len(groups)>ndlg+3) else 'dialogue'
    results[rid]={'kind':kind,'dialogue':ndlg,'fb':total_fb,
                  'ngroups':len(groups),'samples':samples}
    detail.write(f'=== R{rid} kind={kind} dialogue_groups={ndlg} total_groups={len(groups)} fb={total_fb}\n')
    for s in samples:
        detail.write('   sample: '+s+'\n')
detail.close()

# ASCII summary to stdout
for rid in UNTRANS:
    r=results[rid]
    s0=r.get('samples',[''])
    samp=s0[0] if s0 else ''
    print('R%d %-7s dlg=%-3d grp=%-4d fb=%-3d | %s'%(rid,r['kind'],r['dialogue'],r.get('ngroups',0),r.get('fb',0),samp[:50]))

json.dump(results, io.open('build/_shard0_results.json','w',encoding='utf-8'), indent=1, ensure_ascii=True)
print('WROTE build/_shard0_results.json and _shard0_detail.txt')
