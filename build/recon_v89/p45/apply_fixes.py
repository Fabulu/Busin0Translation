#!/usr/bin/env python3
"""Apply Phase 4+5 R1197 bar-scene fixes to data/type2_translated/batch_01.json.
- Re-translate g900-g936 from pristine JP (current EN is fabricated filler).
- Fix g916 choice options (Speak to her / Ignore her).
- Restore capitalization on g5, g931 (regressed vs master).
- Add missing g919 (Lady Knight raw-JP box).
All english is ASCII-only (build_v9 Step 4 skips non-ASCII).
Narration lines <=16 glyphs, BOX lines <=18.  Choice option segments not wrapped.
"""
import json, os
os.chdir('C:/programmieren/wizardrytranslation')
PATH = 'data/type2_translated/batch_01.json'

# msg_index -> new english.  Mode per leak_detector:
#  g900 NARR(box-cap g903-912 BOX), g901-902 NARR, g903 BOX, g904-912 BOX,
#  g913 NARR, g914 BOX, g915 NARR, g916 CHOICE, g917 NARR, g918-925 BOX,
#  g919 BOX(added), g926 NARR, g927-929 BOX, g930 CHOICE, g931 BOX,
#  g932-933 BOX, g934 NARR, g935-936 BOX, g937 NARR.
NEW = {
  900: "I'll pay any / sum. Please look / into what made / Simzon end / up like that.",
  901: "The shopkeeper, / clearing tables / by the door, / and the / knight's words / reached you.",
  902: "She pleaded; he / coolly turned / her away. Such / was the scene.",
  903: "I must know. What / befell Simzon's / band in Karman's / Labyrinth.",
  904: "I will be blunt. / I cannot take / on your request.",
  905: "This tavern only / handles requests / for floors that / mapped parties / have charted.",
  906: "Yet no report / has come that / your comrades' / remains were / found.",
  907: "This is only my / guess, but did / they not press / on to deeper / floors?",
  908: "From the / soldiers' talk, / Simzon's band / were feared as / San-Lazare's / demons.",
  909: "I'd not be / shocked if they / reached the / deepest floors.",
  910: "By now, surely / you understand.",
  911: "Even if I took / your request, / no one could / see it done.",
  912: "I'll spare you / cruel words. Just / wait until they / climb back up.",
  913: "The shopkeeper / held firm. The / knight was left / alone, refused.",
  914: "How could you / know the heart / of one left all / alone! Damn you!",
  915: "She stared into / the void and / murmured, as if / to no one.",
  916: "The knight hangs / her head. // Speak to her / Ignore her",
  917: "You went to the / knight's side / and spoke to / her.",
  918: "...I simply / cannot believe / it.",
  919: "It has been but / ten short days.",
  920: "In the brief / while before I / returned, his / band was wiped / out, and Simzon / became that.",
  921: "I would sooner / accept it had / Simzon simply / died.",
  922: "Famed from the / battlefields of / the rebellion, / feared as / San-Lazare's / demon,",
  923: "courted and / dreaded across / Venoa. I'd not / wish to see him / so broken.",
  924: "That those who / live by the blade / may one day / fall, I do not / dispute.",
  925: "But what could / break the spirit / of so peerless / a warrior?",
  926: "She bit her lip / and turned a / face of deep / sorrow to you.",
  927: "I must know. What / destroyed his / band and stole / the light from / Simzon's eyes.",
  928: "I beg you. Help / me slay the one / behind it.",
  929: "Take me with you / into the maze, / and grant me / the chance to / find the truth.",
  930: "The knight asks / to join you. // Accept / Refuse",
  931: "Thank you. I am / Vera el-Muwahhid.",
  932: "Vera: I am still / a green knight, / but I'll strive / not to be a / burden.",
  933: "I look forward / to serving with / you.",
  934: "Vera joined / your party.",
  935: "I see. A pity.",
  936: "Forgive me for / your time. I'll / seek out / another.",
  937: "Composing / herself, the / knight slipped / out of the / tavern.",
}

# Capitalization-only restores (these groups keep their existing meaning; only
# casing/proper nouns were regressed vs batch_01.json.master).
CAP = {
  5: "I am the owner of / this place. My / name is Gin / Barbus.",
}

def main():
    data = json.load(open(PATH, encoding='utf-8'))
    # index existing R1197 entries
    by_mi = {}
    for e in data:
        if e['resource'] == 1197:
            by_mi[e['msg_index']] = e
    changed = 0
    added = 0
    # apply NEW (re-translations)
    for mi, en in NEW.items():
        if mi in by_mi:
            if by_mi[mi]['english'] != en:
                by_mi[mi]['english'] = en
                changed += 1
        else:
            # need japanese field; pull from corrected dialogue
            jp = CORR.get(mi, '')
            entry = {'resource': 1197, 'msg_index': mi, 'japanese': jp, 'english': en}
            data.append(entry)
            by_mi[mi] = entry
            added += 1
    # apply CAP restores
    for mi, en in CAP.items():
        if mi in by_mi and by_mi[mi]['english'] != en:
            by_mi[mi]['english'] = en
            changed += 1
    # ASCII guard
    bad = []
    for mi, en in list(NEW.items()) + list(CAP.items()):
        for c in en:
            if ord(c) > 127:
                bad.append((mi, c))
    if bad:
        raise SystemExit('NON-ASCII in new english: %r' % bad[:10])
    json.dump(data, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('changed=%d added=%d total entries=%d' % (changed, added, len(data)))

# japanese for any newly-added msg_index (g919)
CORR = {}
def _load_corr():
    d = json.load(open('data/type2_dialogue_corrected.json', encoding='utf-8'))
    for e in d:
        if e.get('resource') == 1197:
            CORR[e['msg_index']] = e.get('japanese', '')
_load_corr()

if __name__ == '__main__':
    main()
