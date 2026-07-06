#!/usr/bin/env python3
"""Shard 0 scan v2: use build_full_english_v2 stream-locating logic to isolate
the REAL glyph stream (payload + extra), then strictly detect natural-language
dialogue. Avoids treating binary Section-1 as glyphs."""
import struct, json, os, io, sys

os.chdir("C:/programmieren/wizardrytranslation")
gmap = json.load(open("data/msg_glyph_map.json", encoding="utf-8"))

# --- helpers inlined verbatim from build/build_full_english_v2.py ---
def count_sequential_table(data, start=16):
    if len(data) < start + 16: return 0
    first = struct.unpack_from('<I', data, start)[0]
    if first != 1: return 0
    count = 0
    for e in range(min(256, (len(data) - start) // 16)):
        eid = struct.unpack_from('<I', data, start + e * 16)[0]
        if eid == e + 1: count = e + 1
        else: break
    return count

def parse_offset_table(data, table_start):
    if table_start + 4 > len(data): return None
    first_val = struct.unpack_from('>H', data, table_start)[0]
    first_flags = struct.unpack_from('>H', data, table_start + 2)[0]
    if first_flags != 0x0000 or first_val < 1 or first_val > 500: return None
    msg_count = first_val; offsets = []; i = table_start + 4
    for e in range(msg_count):
        if i + 4 > len(data): return None
        val = struct.unpack_from('>H', data, i)[0]
        flags = struct.unpack_from('>H', data, i + 2)[0]
        offsets.append(val); i += 4
        if flags == 0xFFFF: break
    return (msg_count, offsets, i - table_start)

def parse_ffff_groups(data, stream_start, stream_end):
    groups = []; grp_start = stream_start; off = stream_start
    while off < stream_end - 1:
        val = struct.unpack_from('>H', data, off)[0]
        if val == 0xFFFF:
            groups.append((grp_start, off)); grp_start = off + 2
        off += 2
    if grp_start < stream_end:
        groups.append((grp_start, stream_end))
    return groups

class V2: pass
v2 = V2()
v2.count_sequential_table = count_sequential_table
v2.parse_offset_table = parse_offset_table
v2.parse_ffff_groups = parse_ffff_groups

def cat_of(ch):
    o = ord(ch)
    if 0x20 <= o < 0x7f: return 'a'
    if 0x3040 <= o <= 0x309f: return 'h'
    if 0x30a0 <= o <= 0x30ff: return 'k'
    if 0x4e00 <= o <= 0x9fff: return 'j'
    if 0xff00 <= o <= 0xffef: return 'f'
    return 'o'

KATA={'ア':'a','イ':'i','ウ':'u','エ':'e','オ':'o','カ':'ka','キ':'ki','ク':'ku','ケ':'ke','コ':'ko',
'サ':'sa','シ':'shi','ス':'su','セ':'se','ソ':'so','タ':'ta','チ':'chi','ツ':'tsu','テ':'te','ト':'to',
'ナ':'na','ニ':'ni','ヌ':'nu','ネ':'ne','ノ':'no','ハ':'ha','ヒ':'hi','フ':'fu','ヘ':'he','ホ':'ho',
'マ':'ma','ミ':'mi','ム':'mu','メ':'me','モ':'mo','ヤ':'ya','ユ':'yu','ヨ':'yo','ラ':'ra','リ':'ri',
'ル':'ru','レ':'re','ロ':'ro','ワ':'wa','ヲ':'wo','ン':'n','ガ':'ga','ギ':'gi','グ':'gu','ゲ':'ge',
'ゴ':'go','ザ':'za','ジ':'ji','ズ':'zu','ゼ':'ze','ゾ':'zo','ダ':'da','ヂ':'di','ヅ':'du','デ':'de',
'ド':'do','バ':'ba','ビ':'bi','ブ':'bu','ベ':'be','ボ':'bo','パ':'pa','ピ':'pi','プ':'pu','ペ':'pe',
'ポ':'po','ー':'-','ァ':'a','ィ':'i','ゥ':'u','ェ':'e','ォ':'o','ッ':'_','ャ':'ya','ュ':'yu','ョ':'yo'}

def decode_words(words):
    chars=[]; cats=[]; mapped=0; unmapped=0; control=0; fb=0
    for g in words:
        if g==0xFFFE:
            chars.append('/'); cats.append('.')
        elif 0xFB00<=g<=0xFB0F:
            fb+=1; control+=1; chars.append(''); cats.append('.')
        elif g>=0xFB00:
            control+=1; chars.append(''); cats.append('.')
        else:
            s=str(g)
            if s in gmap and gmap[s]:
                ch=gmap[s]; chars.append(ch); cats.append(cat_of(ch[0])); mapped+=1
            else:
                chars.append('?'); cats.append('?'); unmapped+=1
    return chars,''.join(cats),mapped,unmapped,control,fb

def longest_lang_run(cats):
    best=cur=best_jp=cur_jp=0
    for c in cats:
        if c in 'ahkjf': cur+=1; best=max(best,cur)
        else: cur=0
        if c in 'hkjf': cur_jp+=1; best_jp=max(best_jp,cur_jp)
        else: cur_jp=0
    return best,best_jp

def gloss(chars):
    out=[]
    for ch in chars:
        if ch in ('','?'): out.append('.') if ch=='?' else None
        elif ch=='/': out.append(' / ')
        else:
            c=ch[0]; o=ord(c)
            if 0x20<=o<0x7f: out.append(c)
            elif c in KATA: out.append(KATA[c])
            elif 0x3040<=o<=0x309f: out.append(KATA.get(chr(o+0x60),'~'))
            elif 0x4e00<=o<=0x9fff: out.append('#')
            else: out.append('~')
    return ''.join(x for x in out if x is not None)[:90]

def get_stream(raw):
    """Replicate v2 stream location. Return list of (msg_idx, words) groups from
    payload AND extra region."""
    h_zero1,h_payload_size,h_stride,h_zero2 = struct.unpack_from('<IIII', raw, 0)
    payload_end = 16 + h_payload_size
    if payload_end>len(raw) or payload_end<16: payload_end=len(raw)
    extra = bytes(raw[payload_end:])
    seq_count = v2.count_sequential_table(raw,16)
    after_seq = 16 + seq_count*16
    ot = v2.parse_offset_table(raw, after_seq)
    if ot is not None:
        _,_,tsize = ot
        stream_start = after_seq+tsize
    else:
        stream_start=None
        for off in range(after_seq, min(len(raw)-1,payload_end),2):
            if struct.unpack_from('>H',raw,off)[0]==0xFFFF:
                stream_start=off; break
        if stream_start is None: stream_start=after_seq
    groups=[]
    # payload groups
    for (gs,ge) in v2.parse_ffff_groups(raw, stream_start, payload_end):
        w=[struct.unpack_from('>H',raw,o)[0] for o in range(gs,ge,2)]
        groups.append(w)
    # extra groups
    if extra and len(extra)>2:
        eb=bytearray(extra)
        for (gs,ge) in v2.parse_ffff_groups(eb,0,len(eb)):
            w=[struct.unpack_from('>H',eb,o)[0] for o in range(gs,ge,2)]
            groups.append(w)
    return groups, stream_start, payload_end, len(raw)

UNTRANS = [680,681,683,684,685,686,687,688,689,691,693,694,695,697,698,699,
701,703,704,705,706,707,708,709,711,713,714,716,717,718,721,723,724,725,727,
729,730,731,732,733,734,735,737,738,739,745,749,751,752,753,754,755,756,759,760]

results={}
detail=io.open('build/_shard0_detail2.txt','w',encoding='utf-8')
for rid in UNTRANS:
    path=f'extracted/packdata_raw/{rid:04d}_type02.raw'
    raw=bytearray(open(path,'rb').read())
    groups, ss, pe, flen = get_stream(raw)
    dlg=0; samples=[]; total_fb=0; textgroups=0
    detail.write(f'=== R{rid} stream_start={ss} payload_end={pe} flen={flen} ngroups={len(groups)}\n')
    for gi,w in enumerate(groups):
        if not w: continue
        chars,cats,mapped,unmapped,control,fb=decode_words(w)
        total_fb+=fb
        langlen=sum(1 for c in cats if c in 'ahkjf')
        if langlen==0: continue
        textgroups+=1
        run,run_jp=longest_lang_run(cats)
        # strict natural-language test:
        # require a solid contiguous jp run OR ascii word, AND that mapped
        # glyphs strongly outnumber unmapped within the group's language span.
        denom=mapped+unmapped
        hit=mapped/denom if denom else 0
        is_dlg=False
        if run_jp>=5 and hit>=0.7: is_dlg=True
        elif run_jp>=8 and hit>=0.55: is_dlg=True
        elif run>=8 and mapped>=8 and hit>=0.7 and unmapped<=2: is_dlg=True
        if is_dlg:
            dlg+=1
            g=gloss(chars)
            detail.write(f'  [g{gi}] mapped={mapped} unmapped={unmapped} run={run} runjp={run_jp} hit={hit:.2f} fb={fb}\n')
            detail.write('     '+g+'\n')
            if len(samples)<5: samples.append(g)
    if dlg==0: kind='binary'
    elif textgroups>dlg+5: kind='mixed'
    else: kind='dialogue'
    results[rid]={'kind':kind,'dialogue':dlg,'textgroups':textgroups,'fb':total_fb,
                  'ngroups':len(groups),'samples':samples}

for rid in UNTRANS:
    r=results[rid]; s=r['samples'][0] if r['samples'] else ''
    print('R%d %-8s dlg=%-3d txtg=%-3d grp=%-4d fb=%-4d | %s'%(rid,r['kind'],r['dialogue'],r['textgroups'],r['ngroups'],r['fb'],s[:45]))
detail.close()
json.dump(results, io.open('build/_shard0_results2.json','w',encoding='utf-8'), indent=1, ensure_ascii=True)
print('DONE')
