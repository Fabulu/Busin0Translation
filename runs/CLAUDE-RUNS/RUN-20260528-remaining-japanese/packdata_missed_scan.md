# PACKDATA Missed Text Scan Results

Scan date: 2026-05-28
Method: Consecutive glyph-run detection with Japanese content filtering, manual review of results.

## Already Translated
- R34 (type-01): Character creation menus
- R35 (type-01): Character creation menus  
- R38 (type-01): System/game menus
- R39 (type-01): System/game menus
- R2124 (type-01): Additional text
- R2654 (type-02): Additional text

## Excluded (unsafe to patch)
- R1053 (type-03), R1908 (type-06)

## Type-02 (MSG) Resources
- 617 total type-02 resources in PACKDATA
- 124 currently patched via the MSG translation pipeline
- Remaining 493 type-02 resources are handled by the main pipeline (translation queue)
- R842 (type-02) and R752 (type-02) flagged by scan but are normal MSG resources -- pipeline will reach them

---

## FINDINGS: Untranslated Type-01 System Menus (R34-R49)

These are the **highest priority** missed resources. All contain clearly readable Japanese game text.

### R36 (type-01, 3390 bytes) -- NOT TRANSLATED
- Content: Appears to be NPC/scenario text, item or monster names
- Sample: "バブリースライム" (Bubbly Slime), system text with particles
- JP chars: 985, text runs: 138

### R37 (type-01, 2908 bytes) -- NOT TRANSLATED
- Content: Character creation screens
- Sample: "名前を入力してください。" (Please enter a name), "性別を選んでください。" (Please select gender), "種族を選んでください。" (Please select race)
- JP chars: 581, text runs: 84

### R40 (type-01, 2034 bytes) -- NOT TRANSLATED
- Content: Adventurer's Guild text
- Sample: "ようこそ、冒険者よ" (Welcome, adventurer), "冒険者登録を開いてやろう" (Let me open adventurer registration), "おや、もう出て行くのか？" (Oh, leaving already?)
- JP chars: 737, text runs: 72

### R41 (type-01, 1000 bytes) -- NOT TRANSLATED
- Content: Salem Church text
- Sample: "ここはサレム教会。" (This is Salem Church), "サレム教会へようこそ。" (Welcome to Salem Church)
- JP chars: 391, text runs: 40

### R42 (type-01, 614 bytes) -- NOT TRANSLATED
- Content: Adventurer's Inn text
- Sample: "冒険者の宿へようこそ。" (Welcome to the Adventurer's Inn), "ここは心身を帰め、" (This is a place to rest body and soul)
- JP chars: 224, text runs: 23

### R43 (type-01, 1416 bytes) -- NOT TRANSLATED
- Content: Tavern/quest text
- Sample: "おうおう、" (Hey hey), "あの依頼はどうなった？" (How did that request go?), "一杯ひっかけてくかい？" (Wanna grab a drink?), "掲鉄板を見るのか？" (Looking at the bulletin board?)
- JP chars: 433, text runs: 50

### R44 (type-01, 2306 bytes) -- NOT TRANSLATED
- Content: Shop/service NPC text
- Sample: "よく来てくださいました。" (Thank you for coming), "冒書事に御用を" (What business do you need?), "お待ちしておりましたよ。" (We've been waiting for you), "オートマターの調子は" (How is the Automater doing?)
- JP chars: 815, text runs: 87

### R45 (type-01, 6950 bytes) -- NOT TRANSLATED
- Content: Vigor's Shop text (weapon/item shop)
- Sample: "ヴィガーしょうてんにようこそ" (Welcome to Vigor's Shop), "バリバリはたらくだよ" (I'm working hard), "うりたいものがあったら" (If you have something to sell)
- JP chars: 2237, text runs: 262

### R48 (type-01, 2186 bytes) -- NOT TRANSLATED
- Content: Dungeon/adventure text
- Sample: "不法投棄場" (Illegal Dumping Ground), text about adventures, quests
- JP chars: 638, text runs: 96

### R49 (type-01, 3458 bytes) -- NOT TRANSLATED
- Content: Dungeon interaction text (switches, walls, doors)
- Sample: "特に変わったところはない" (Nothing unusual here), "こちらからは開きそうにない" (It doesn't look like it'll open from this side), "もろくて崩れそうなカベだ" (A fragile, crumbling wall), "スイッチがoffになっている。" (The switch is off), "スイッチをonにした" (Turned the switch on)
- JP chars: 1240, text runs: 119

---

## FINDINGS: Non-Menu Type-01 Resources

### R46 (type-03, 18740 bytes) -- NOT TRANSLATED
- Content: Bulletin board / message board system text
- Sample: "この度、ドゥーハン器民のみなさまが" (Dear citizens of Duhan), "気素に払見交更を行えるよう、" (So you can easily exchange...), "掲鉄板にメッセージを残したい方は" (If you'd like to leave a message on the bulletin board)
- JP chars: 7767, text runs: 647
- NOTE: This is type-03, not the typical MSG format. Needs special handling.

### R47 (type-03, 1962 bytes) -- NOT TRANSLATED
- Content: Combat encounter text
- Sample: "元品的なモンスターだ！！" (A formidable monster!!), "立ち去る" (Leave), "モンスターの不払をついた" (Caught the monster off guard), "モンスターは突然おそいかかってきた" (The monster suddenly attacked)
- JP chars: 550, text runs: 56
- NOTE: Also type-03. Needs special handling.

---

## FALSE POSITIVES (confirmed NOT translatable text)

The following were flagged by the scan but are binary/3D data with coincidental glyph hits:

- Large type-01 resources (60KB-315KB): R786, R1215, R1256, R1286, R1302, R1310, R2288, R2363, R2401, R2418, R2485-R2491, R2523, R2774, R2779, R2833, R2860
  - Decoded text is gibberish/repetitive patterns like "ベベベベベ" or random kanji
  - These are 3D model data, texture data, or other binary formats
- 1,158 "Category B" resources: All produce repetitive single-character patterns -- binary data

- Non-standard types (type-03 through type-57): Mostly produce gibberish patterns like "４ち下二" -- structural binary data

---

## Summary

| Category | Count | Action |
|----------|-------|--------|
| System menu text (R36-R49, not translated) | 10 | HIGH PRIORITY - translate these |
| Type-03 game text (R46, R47) | 2 | HIGH PRIORITY - needs format RE |
| Type-02 MSG (normal pipeline) | ~493 remaining | Continue with existing pipeline |
| Binary/3D data false positives | ~1,300+ | No action needed |

### Action Items

High Priority -- System menus players will see immediately:
- [ ] R37: Character creation text
- [ ] R40: Adventurer's Guild
- [ ] R41: Salem Church
- [ ] R42: Adventurer's Inn
- [ ] R43: Tavern/Quests
- [ ] R44: Shop/service NPCs
- [ ] R45: Vigor's Shop (largest, 6950 bytes)
- [ ] R48: Dungeon locations
- [ ] R49: Dungeon interactions (switches, walls, doors)
- [ ] R36: NPC/scenario text

High Priority -- Game text in non-MSG format:
- [ ] R46 (type-03): Bulletin board system (7767 JP chars -- largest untranslated resource)
- [ ] R47 (type-03): Combat encounter text

Already done: R34, R35, R38, R39, R2124, R2654
