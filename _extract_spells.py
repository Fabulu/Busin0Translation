import json, re
d = json.load(open('data/r34_english_aligned.json', encoding='utf-8'))
ents = [e for e in d['entries'] if e['sub'] == 9 and e['jp'].replace('/', '').strip()]
fix = [('騎事持騎法', '魔術師魔法'), ('神今騎法', '神官魔法'), ('[0x03DC]開', '即死'),
       ('者箱', '戦闘'), ('宝', '敵'), ('限帯', '雷属'), ('禍帯', '氷属'),
       ('炎帯', '炎属'), ('汝帯', '聖属'), ('習下', '習得'), ('騎法団', '魔法書'),
       ('騎法', '魔法'), ('ダメ}ジ', 'ダメージ'), ('ステ}タス', 'ステータス'),
       ('用新', '味方'), ('余開彼', '不死系'), ('解消力', '防御力'), ('回声力', '回避力'),
       ('獲得力', '攻撃力'), ('上羽', '上昇'), ('高下', '低下'), ('好所', '吸収'),
       ('制れ', '痺れ'), ('発達', '効果')]
def clean(s):
    for a, b in fix:
        s = s.replace(a, b)
    return s
out = []
fjp = open('_spells_jp.txt', 'w', encoding='utf-8')
for e in ents:
    jp = e['jp']
    en = e.get('english', '')
    m = re.search(r'teaches ([A-Za-z][\w \'-]*)', en)
    name = m.group(1).strip().rstrip('.') if m else ''
    cj = clean(jp)
    school = 'Mage Magic' if '魔術師' in cj else ('Holy Magic' if '神官' in cj else '?')
    lvm = re.search(r'レベル(\d)', jp)
    lv = lvm.group(1) if lvm else '?'
    fjp.write('msg%d L%s %s | %s | %s\n' % (e['msg'], lv, school, name, cj.replace('\n', ' ')))
    out.append({'id': 'R34:s9:msg%d' % e['msg'], 'name': name, 'school': school, 'lv': lv, 'jp': cj, 'en': en})
fjp.close()
json.dump(out, open('_spells_full.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('total spells', len(out))
for o in out:
    print(o['id'], 'L' + o['lv'], o['school'][:4], '::', o['name'])
