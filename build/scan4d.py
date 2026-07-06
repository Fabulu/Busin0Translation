# -*- coding: utf-8 -*-
import json
d=json.load(open('data/type2_translated/batch_r39_equip_b.json',encoding='utf-8'))
ids=[557,558,624,631,638,559,561,578]
with open('build/scan4d_out.txt','w',encoding='utf-8') as w:
    for rec in d:
        m=rec.get('msg_index')
        if m in ids:
            jp=rec.get('japanese','')
            cps=' '.join('U+%04X'%ord(c) for c in jp)
            w.write('m%-4s en=%-25r jp_codepoints=%s\n'%(m,rec.get('english',''),cps))
print('ok')
