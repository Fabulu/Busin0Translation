# Mirror Step 2's encoding to count words exactly. ASCII only.
import json, struct, sys

def word_wrap(text, max_chars=18):
    segments = text.split(' / ')
    wrapped = []
    for seg in segments:
        while len(seg) > max_chars:
            brk = seg.rfind(' ', 0, max_chars + 1)
            if brk <= 0:
                brk = max_chars
            wrapped.append(seg[:brk])
            seg = seg[brk:].lstrip(' ')
        wrapped.append(seg)
    return ' / '.join(wrapped)

def count_words(en, lead_ctrl_words=0):
    en = word_wrap(en)
    n = lead_ctrl_words
    for pi, pt in enumerate(en.split(' / ')):
        if pi > 0:
            n += 1  # 0xFFFE
        for c in pt:
            n += 1  # glyph
    return n, word_wrap(en)

BUDGETS = {1888:148,1889:138,1890:116,1891:89,1892:34,1893:141,1894:43}  # 1894 has 0xFFF1 lead, so 44-1=43 text budget

def check(mi, en):
    lead = 0  # ctrl is auto-prepended by Step2, NOT part of our english
    n, ww = count_words(en, 0)
    # for 1894, the 0xFFF1 is auto-added so effective budget for our text = full ocs/2 minus 1
    cap = BUDGETS[mi]
    ok = n <= cap
    print(f"mi{mi}: words={n} cap={cap} {'OK' if ok else 'OVER by '+str(n-cap)}  chars={len(en)}")
    return ok

if __name__ == '__main__':
    d = json.load(open(sys.argv[1], encoding='utf-8'))
    allok=True
    for e in d:
        if e.get('resource')==2654 and 1888<=e.get('message',0)<=1894:
            allok &= check(e['message'], e['english'])
    print('ALL OK' if allok else 'SOME OVER BUDGET')
