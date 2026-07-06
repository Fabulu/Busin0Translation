# -*- coding: utf-8 -*-
import json, os, re

SHARD_FILES = [
 'data/translate_chunks/chunk_00.json',
 'data/translate_chunks/chunk_01_translated.json',
 'data/translate_chunks/chunk_03.json',
 'data/translate_chunks/chunk_04_translated.json',
 'data/translate_chunks/chunk_06.json',
 'data/translate_chunks/chunk_07_translated.json',
 'data/translate_chunks/chunk_09.json',
 'data/translate_chunks/chunk_r34_fix.json',
 'data/translate_chunks/chunk_r37_extra.json',
 'data/translate_chunks/chunk_r38_fix_no_gender.json',
 'data/translate_chunks/chunk_r43_fix.json',
 'data/type2_translated/batch_02.json',
 'data/type2_translated/batch_05.json',
 'data/type2_translated/batch_08.json',
 'data/type2_translated/batch_11.json',
 'data/type2_translated/batch_gap1347.json',
 'data/type2_translated/batch_intro_narration.json',
 'data/type2_translated/batch_r1168_1173.json',
 'data/type2_translated/batch_r39_equip_b.json',
]

# JP length: count CJK chars (each ~ 1 cell, dense). EN length: chars.
def jp_len(s):
    return sum(1 for c in s if ord(c) > 0x2000)

# barker/prompt/menu keyword signals
PROMPT_KW = re.compile(r"\b(business|what do you|what is your|may i help|how can i help|welcome|yes/no|are you sure|do you want|would you like|what'll it be|choose|select|cancel|confirm|leave|enter|farewell|good luck|come again|see you|anything else|need something|looking for)\b", re.I)
QMARK = re.compile(r"\?\s*$")

def longest_line(en):
    # consider authored breaks
    parts = re.split(r" // | / |\n", en)
    return max((len(p.strip()) for p in parts), default=len(en))

out = []
for f in SHARD_FILES:
    if not os.path.exists(f):
        continue
    d = json.load(open(f, encoding='utf-8'))
    if not isinstance(d, list):
        continue
    for rec in d:
        en = rec.get('english')
        jp = rec.get('japanese','')
        if not en or not isinstance(en, str):
            continue
        en_s = en.strip()
        if not en_s:
            continue
        jl = jp_len(jp)
        el = len(en_s)
        ll = longest_line(en_s)
        has_break = (' // ' in en_s) or (' / ' in en_s)
        looks_prompt = bool(PROMPT_KW.search(en_s)) or bool(QMARK.search(en_s))
        # overflow heuristic: single-line (no authored break) and long-ish, esp. prompts
        # Narrow boxes: a prompt/barker line. Flag if longest line > 24 chars and no break,
        # or EN much longer than JP would render.
        ratio = (el / jl) if jl else 99
        flag = False
        reason = []
        if not has_break and ll > 26:
            if looks_prompt:
                flag = True; reason.append('prompt_longline')
            elif jl and jl <= 16 and el > 30:
                flag = True; reason.append('bloat_short_jp')
            elif ll > 34:
                flag = True; reason.append('very_long_singleline')
        if flag:
            key = f"R{rec.get('resource')}_M{rec.get('message', rec.get('msg_index'))}"
            out.append((f, key, en_s, jl, el, ll, ';'.join(reason)))

out.sort(key=lambda x: -x[5])
print("CANDIDATES", len(out))
with open('build/_shard0_candidates.json','w',encoding='utf-8') as w:
    json.dump([{'file':o[0],'key':o[1],'en':o[2],'jp_len':o[3],'en_len':o[4],'longest':o[5],'reason':o[6]} for o in out], w, ensure_ascii=False, indent=1)
# ASCII summary
for o in out[:80]:
    safe = o[2].encode('ascii','replace').decode()
    print(f"{o[5]:3d} {o[6]:22s} {o[1]:14s} {safe[:70]}")
