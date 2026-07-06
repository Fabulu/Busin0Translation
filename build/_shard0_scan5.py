#!/usr/bin/env python3
"""Shard 0 scan v5 (FINAL): glyph-variety discriminator.
Calibrated on R1196 (real dialogue: run rep ratio 0.5-1.0) vs dungeon files
(runs are 1-2 glyph repetitions, rep 0.0-0.11 = binary fill).
A real text run = contiguous valid-glyph run with length>=6, rep(unique/len)>=0.5,
and >=2 kana. Reports genuine dialogue message-group count + ASCII glosses."""
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

def gl(ch):
    c=ch[0];o=ord(c)
    if 0x20<=o<0x7f: return c
    if c in KATA: return KATA[c]
    if 0x3040<=o<=0x309f: return KATA.get(chr(o+0x60),'~')
    if 0x4e00<=o<=0x9fff: return '#'
    return '~'

def is_ctrl(w): return w==0xFFFE or w==0xFFFF or (0xFB00<=w<=0xFB0F)
def gchar(w):
    s=str(w)
    if s in gmap and gmap[s]: return gmap[s]
    return None

def scan_runs(words):
    """Contiguous runs of (glyph or control). Yield dict per run."""
    out=[]; i=0; n=len(words)
    while i<n:
        if gchar(words[i]) is not None and not is_ctrl(words[i]):
            j=i; gids=[]; chars=[]; kana=kanji=0; fb=0; subsep=0
            while j<n and (gchar(words[j]) is not None or is_ctrl(words[j])):
                w=words[j]
                if w==0xFFFE: chars.append('/'); j+=1; continue
                if w==0xFFFF: chars.append('|'); subsep+=1; j+=1; continue
                if 0xFB00<=w<=0xFB0F: chars.append('<S>'); fb+=1; j+=1; continue
                ch=gchar(w); gids.append(w); chars.append(gl(ch))
                o=ord(ch[0])
                if 0x3040<=o<=0x309f or 0x30a0<=o<=0x30ff: kana+=1
                elif 0x4e00<=o<=0x9fff: kanji+=1
                j+=1
            L=len(gids); rep=(len(set(gids))/L) if L else 0
            out.append(dict(start=i,glyphs=L,rep=rep,kana=kana,kanji=kanji,
                            fb=fb,subsep=subsep,text=''.join(chars)))
            i=max(j,i+1)
        else: i+=1
    return out

UNTRANS = [680,681,683,684,685,686,687,688,689,691,693,694,695,697,698,699,
701,703,704,705,706,707,708,709,711,713,714,716,717,718,721,723,724,725,727,
729,730,731,732,733,734,735,737,738,739,745,749,751,752,753,754,755,756,759,760]

results={}; detail=io.open('build/_shard0_detail5.txt','w',encoding='utf-8')
for rid in UNTRANS:
    path=f'extracted/packdata_raw/{rid:04d}_type02.raw'
    raw=open(path,'rb').read()
    words=[struct.unpack_from('>H',raw,2*i)[0] for i in range(len(raw)//2)]
    runs=scan_runs(words)
    real=[r for r in runs if r['glyphs']>=6 and r['rep']>=0.5 and r['kana']>=2]
    # message-group count: each real run's FFFF-delimited subsegments with text
    msgs=0; samples=[]
    detail.write(f'=== R{rid} flen={len(raw)} real_runs={len(real)}\n')
    for r in real:
        segs=[s for s in r['text'].split('|') if any(ch.isalnum() or ch in '#~' for ch in s)]
        msgs+=max(1,len(segs))
        detail.write(f'  @w{r["start"]} g={r["glyphs"]} rep={r["rep"]:.2f} kana={r["kana"]} kanji={r["kanji"]} fb={r["fb"]}\n')
        detail.write('     '+r['text'][:220]+'\n')
        if len(samples)<6: samples.append(r['text'][:90])
    kind = 'binary' if msgs==0 else ('mixed' if len(real) < 0.5*len(runs) or len(raw)>50000 else 'dialogue')
    results[rid]=dict(kind=kind,dialogue=msgs,real_runs=len(real),
                      total_runs=len(runs),flen=len(raw),samples=samples)

nz=0
for rid in UNTRANS:
    r=results[rid]; s=r['samples'][0] if r['samples'] else ''
    if r['dialogue']>0: nz+=1
    print('R%d %-7s dlg=%-3d realruns=%-3d/%-4d flen=%-8d | %s'%(
        rid,r['kind'],r['dialogue'],r['real_runs'],r['total_runs'],r['flen'],s[:40]))
detail.close()
json.dump(results,io.open('build/_shard0_results5.json','w',encoding='utf-8'),indent=1,ensure_ascii=True)
print('resources with dialogue>0:',nz,'of',len(UNTRANS))
print('DONE')
