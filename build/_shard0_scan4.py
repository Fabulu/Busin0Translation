#!/usr/bin/env python3
"""Shard 0 scan v4: precise sparse-dialogue detector.
A real text run = contiguous span (ZERO gap) of words that are each a valid
glyph gid (0..1750-ish in map) or a control (FFFE/FFFF/FB00-0F), AND the span
contains >=2 kana (particles) and >=6 total glyphs. Binary coordinate data
breaks such spans almost immediately (values >1750 are invalid), so this
isolates genuine natural-language text even when sparse (1-3 messages)."""
import struct, json, os, io

os.chdir("C:/programmieren/wizardrytranslation")
gmap = json.load(open("data/msg_glyph_map.json", encoding="utf-8"))

KATA={'ア':'a','イ':'i','ウ':'u','エ':'e','オ':'o','カ':'ka','キ':'ki','ク':'ku','ケ':'ke','コ':'ko',
'サ':'sa','シ':'shi','ス':'su','セ':'se','ソ':'so','タ':'ta','チ':'chi','ツ':'tsu','テ':'te','ト':'to',
'ナ':'na','ニ':'ni','ヌ':'nu','ネ':'ne','ノ':'no','ハ':'ha','ヒ':'hi','フ':'fu','ヘ':'he','ホ':'ho',
'マ':'ma','ミ':'mi','ム':'mu','メ':'me','モ':'mo','ヤ':'ya','ユ':'yu','ヨ':'yo','ラ':'ra','リ':'ri',
'ル':'ru','レ':'re','ロ':'ro','ワ':'wa','ヲ':'wo','ン':'n','ガ':'ga','ギ':'gi','グ':'gu','ゲ':'ge',
'ゴ':'go','ザ':'za','ジ':'ji','ズ':'zu','ゼ':'ze','ゾ':'zo','ダ':'da','ヂ':'di','ヅ':'du','デ':'de',
'ド':'do','バ':'ba','ビ':'bi','ブ':'bu','ベ':'be','ボ':'bo','パ':'pa','ピ':'pi','プ':'pu','ペ':'pe',
'ポ':'po','ー':'-','ァ':'a','ィ':'i','ゥ':'u','ェ':'e','ォ':'o','ッ':'_','ャ':'ya','ュ':'yu','ョ':'yo',
'。':'.','、':',','「':'[','」':']','・':'.'}

def cls(w):
    if w==0xFFFE: return ('lb',None)
    if w==0xFFFF: return ('gend',None)
    if 0xFB00<=w<=0xFB0F: return ('fb',None)
    if w>=0xFB00: return ('bad',None)
    s=str(w)
    if s in gmap and gmap[s]:
        ch=gmap[s]; o=ord(ch[0])
        if 0x3040<=o<=0x309f or 0x30a0<=o<=0x30ff: return ('kana',ch)
        if 0x4e00<=o<=0x9fff: return ('kanji',ch)
        if 0x20<=o<0x7f: return ('ascii',ch)
        return ('other',ch)
    return ('bad',None)

def gl(ch):
    if ch is None: return ''
    c=ch[0]; o=ord(c)
    if 0x20<=o<0x7f: return c
    if c in KATA: return KATA[c]
    if 0x3040<=o<=0x309f: return KATA.get(chr(o+0x60),'~')
    if 0x4e00<=o<=0x9fff: return '#'
    return '~'

def find_text_runs(words):
    """Zero-gap runs of valid glyph/control words. Returns list of dicts."""
    runs=[]
    i=0; n=len(words)
    while i<n:
        k,ch=cls(words[i])
        if k in ('kana','kanji','ascii','other','fb'):
            j=i; chars=[]; kana=kanji=ascii_=fb=glyphs=0
            seps=0
            while j<n:
                kk,cc=cls(words[j])
                if kk=='bad': break
                if kk=='gend':
                    # group end inside a run -> allow, marks message boundary
                    chars.append('|'); seps+=1; j+=1; continue
                if kk=='lb': chars.append('/'); j+=1; continue
                if kk=='fb': chars.append('<S>'); fb+=1; j+=1; continue
                # glyph
                chars.append(gl(cc)); glyphs+=1
                if kk=='kana': kana+=1
                elif kk=='kanji': kanji+=1
                elif kk=='ascii': ascii_+=1
                j+=1
            runs.append(dict(start=i,end=j,glyphs=glyphs,kana=kana,kanji=kanji,
                             ascii=ascii_,fb=fb,seps=seps,text=''.join(chars)))
            i=max(j,i+1)
        else:
            i+=1
    return runs

UNTRANS = [680,681,683,684,685,686,687,688,689,691,693,694,695,697,698,699,
701,703,704,705,706,707,708,709,711,713,714,716,717,718,721,723,724,725,727,
729,730,731,732,733,734,735,737,738,739,745,749,751,752,753,754,755,756,759,760]

results={}
detail=io.open('build/_shard0_detail4.txt','w',encoding='utf-8')
for rid in UNTRANS:
    path=f'extracted/packdata_raw/{rid:04d}_type02.raw'
    raw=open(path,'rb').read()
    nw=len(raw)//2
    words=[struct.unpack_from('>H',raw,2*i)[0] for i in range(nw)]
    runs=find_text_runs(words)
    # A genuine natural-language run: glyphs>=6 AND kana>=2 AND
    # (kana+kanji) >= glyphs*0.5 (text not dominated by ascii digits/coords)
    real=[]
    for r in runs:
        if r['glyphs']>=6 and r['kana']>=2 and (r['kana']+r['kanji'])>=r['glyphs']*0.5:
            real.append(r)
    # count dialogue message groups: split each real run on '|' separators +1,
    # but also use fb tags. Use number of '|'-delimited subsegments with text.
    msg_count=0
    samples=[]
    detail.write(f'=== R{rid} flen={len(raw)} real_runs={len(real)}\n')
    for r in real:
        subsegs=[s for s in r['text'].split('|') if any(c.isalnum() or c in '#~' for c in s)]
        msg_count+=max(1,len(subsegs))
        detail.write(f'  @w{r["start"]} glyphs={r["glyphs"]} kana={r["kana"]} kanji={r["kanji"]} fb={r["fb"]} seps={r["seps"]}\n')
        detail.write('     '+r['text'][:200]+'\n')
        if len(samples)<6:
            samples.append(r['text'][:90])
    if msg_count==0:
        kind='binary'
    else:
        # nearly all these files are huge binary with sparse text -> mixed
        kind='mixed' if len(raw)>50000 else ('dialogue' if msg_count>=2 else 'mixed')
    results[rid]=dict(kind=kind,dialogue=msg_count,real_runs=len(real),
                      flen=len(raw),samples=samples)

for rid in UNTRANS:
    r=results[rid]; s=r['samples'][0] if r['samples'] else ''
    print('R%d %-7s dlg=%-3d runs=%-3d flen=%-8d | %s'%(rid,r['kind'],r['dialogue'],r['real_runs'],r['flen'],s[:45]))
detail.close()
json.dump(results,io.open('build/_shard0_results4.json','w',encoding='utf-8'),indent=1,ensure_ascii=True)
print('DONE')
