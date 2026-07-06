#!/usr/bin/env python3
"""Shard 0 scan v3: structure-agnostic. Scan whole file as BE u16 words and find
DENSE contiguous runs of valid glyphs (real text). A run = maximal span where
words are valid glyph ids (mapped kana/kanji/ascii, or FFFE/FFFF/FB control)
with a HIGH fraction mapped. Real dialogue regions show up as long high-density
runs; binary noise gives only short scattered hits."""
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

def kind_of(w):
    """Return ('map',ch) | ('ctrl',None) | ('none',None)."""
    if w==0xFFFE or w==0xFFFF: return ('ctrl',None)
    if 0xFB00<=w<=0xFB0F: return ('fb',None)
    if w>=0xFB00: return ('none',None)
    s=str(w)
    if s in gmap and gmap[s]: return ('map',gmap[s])
    return ('none',None)

def gloss(chars):
    out=[]
    for ch in chars:
        if ch is None: out.append('.'); continue
        if ch=='\x01': out.append(' / '); continue
        if ch=='\x02': out.append('<S>'); continue
        c=ch[0]; o=ord(c)
        if 0x20<=o<0x7f: out.append(c)
        elif c in KATA: out.append(KATA[c])
        elif 0x3040<=o<=0x309f: out.append(KATA.get(chr(o+0x60),'~'))
        elif 0x4e00<=o<=0x9fff: out.append('#')
        else: out.append('~')
    return ''.join(out)

def find_runs(words):
    """Find maximal runs of glyph-words. Tolerate up to 1 'none' between maps.
    Return list of (start,end_excl,n_map,n_fb,chars)."""
    runs=[]
    i=0; n=len(words)
    while i<n:
        k,ch=kind_of(words[i])
        if k=='map':
            j=i; nmap=0; nfb=0; chars=[]; gap=0; last_map=i
            while j<n:
                kk,cc=kind_of(words[j])
                if kk=='map':
                    nmap+=1; chars.append(cc); gap=0; last_map=j
                elif kk=='fb':
                    nfb+=1; chars.append('\x02'); gap=0
                elif kk=='ctrl':
                    chars.append('\x01' if words[j]==0xFFFE else '\x01'); gap=0
                else:
                    gap+=1
                    if gap>1: break
                    chars.append(None)
                j+=1
            # trim trailing non-map
            end=last_map+1
            runs.append((i,end,nmap,nfb,chars[:end-i]))
            i=max(end,i+1)
        else:
            i+=1
    return runs

UNTRANS = [680,681,683,684,685,686,687,688,689,691,693,694,695,697,698,699,
701,703,704,705,706,707,708,709,711,713,714,716,717,718,721,723,724,725,727,
729,730,731,732,733,734,735,737,738,739,745,749,751,752,753,754,755,756,759,760]

MINRUN=8  # minimum mapped glyphs to count a run as real text

results={}
detail=io.open('build/_shard0_detail3.txt','w',encoding='utf-8')
for rid in UNTRANS:
    path=f'extracted/packdata_raw/{rid:04d}_type02.raw'
    raw=open(path,'rb').read()
    nw=len(raw)//2
    words=[struct.unpack_from('>H',raw,2*i)[0] for i in range(nw)]
    runs=find_runs(words)
    # keep substantial runs
    big=[r for r in runs if r[2]>=MINRUN]
    total_map=sum(r[2] for r in big)
    total_fb_in_runs=sum(r[3] for r in big)
    samples=[]
    detail.write(f'=== R{rid} flen={len(raw)} big_runs={len(big)} total_mapped={total_map}\n')
    for (s,e,nm,nf,chars) in big[:40]:
        g=gloss(chars)
        detail.write(f'  @word{s} mapped={nm} fb={nf} len={e-s}: {g[:120]}\n')
        if len(samples)<6 and nm>=8:
            samples.append(g[:90])
    # dialogue message-group count: count FB speaker tags inside big runs as a
    # proxy for message boundaries; if no FB, count the runs themselves.
    if total_fb_in_runs>0:
        dlg=total_fb_in_runs
    else:
        dlg=len(big)
    if len(big)==0:
        kind='binary'; dlg=0
    elif total_map < 30 and len(big)<=2:
        kind='binary'; dlg=0  # only incidental
    else:
        # mixed: huge file with binary plus some text
        kind='mixed'
    results[rid]={'kind':kind,'dialogue':dlg,'big_runs':len(big),
                  'total_mapped':total_map,'fb_in_runs':total_fb_in_runs,
                  'flen':len(raw),'samples':samples}

for rid in UNTRANS:
    r=results[rid]; s=r['samples'][0] if r['samples'] else ''
    print('R%d %-7s dlg=%-4d runs=%-3d map=%-5d fbR=%-4d | %s'%(
        rid,r['kind'],r['dialogue'],r['big_runs'],r['total_mapped'],r['fb_in_runs'],s[:42]))
detail.close()
json.dump(results, io.open('build/_shard0_results3.json','w',encoding='utf-8'),indent=1,ensure_ascii=True)
print('DONE')
