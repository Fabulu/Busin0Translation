# -*- coding: utf-8 -*-
import json
d=json.load(open('data/type2_translated/batch_r39_equip_b.json',encoding='utf-8'))
# show item-like records with japanese, romanized check via codepoints
ids=[423,557,558,559,561,578,624,625,626,627,628,629,630,631,632,633,634,635,636,637,638,639,640,641,642,643,644]
def jpinfo(s):
    # count CJK chars
    return sum(1 for c in s if ord(c)>0x3000)
with open('build/scan4c_out.txt','w',encoding='utf-8') as w:
    for rec in d:
        m=rec.get('msg_index')
        if m in ids:
            e=rec.get('english','')
            jp=rec.get('japanese','')
            w.write('m%-4s en=%-25r jpchars=%d jp_glyphs~%d\n'%(m,e,len(jp),jpinfo(jp)))
print('ok')
