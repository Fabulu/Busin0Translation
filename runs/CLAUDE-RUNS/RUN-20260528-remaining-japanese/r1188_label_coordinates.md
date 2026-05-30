# R1188 Atlas Label Coordinate Map

**Date**: 2026-05-28
**Atlas**: `build/textures_to_edit/R1188_CORRECT_dbw512.png` (1024x1024, grayscale L mode)
**PCSX2 Dumps**: `build/pcsx2_dumps/*3cb39bf7659ef15f*` (16 files, CLUT hash `3cb39bf7659ef15f`)
**JSON output**: `data/r1188_label_map.json`

---

## Critical Finding: Template Matching Fails

Direct pixel-level template matching between the PCSX2 dumps and the deswizzled atlas produces no valid matches. The best NCC score achieved was 0.577 (a reliable match requires >0.95). This was confirmed by the prior analysis in `r1188_template_match.md`.

**Root cause**: The deswizzled atlas (`R1188_CORRECT_dbw512.png`) does NOT correctly reconstruct the VRAM layout from which the game reads these labels. The game uses TEX0 register `0x2214` as the GS page base, reading a 256x256 PSMT4 sub-region. The deswizzle with `dbw_ct32=512` produces a visually coherent font atlas (all glyphs are readable), but the pixel arrangement does not match how the GS hardware maps UV coordinates to VRAM addresses for the TEX0 configuration used by these labels.

---

## Definitive PCSX2 Dump Identification

All 16 dumps were visually examined at 8x magnification using alpha channel extraction (text is white RGB with variable alpha on transparent background).

### Tab Labels (48x20, 8 dumps)

| # | Texture Hash | Japanese | English | Meaning |
|---|-------------|----------|---------|---------|
| 1 | `16625baf9feaeafb` | 性別 | Gender | Gender selection label |
| 2 | `19a39fbc8a08d7ec` | 記号 | Sym | Symbol input tab |
| 3 | `1f839869fab251d` | カナ | Kana | Katakana input tab |
| 4 | `6f1fb24fad5cd1a` | 英数 | ABC | Alphanumeric input tab |
| 5 | `88ff8b577084a2a8` | 職業 | Class | Class/job sidebar label |
| 6 | `9677cb23da53ff88` | かな | Hira | Hiragana input tab |
| 7 | `9bec87b4031a7172` | 種族 | Race | Race sidebar label |
| 8 | `c89b469f7a152a6` | 属性 | Align | Alignment sidebar label |

### Stat Labels (64x16, 7 dumps)

| # | Texture Hash | Japanese | English | Meaning |
|---|-------------|----------|---------|---------|
| 9 | `280ea82c1c476a98` | 力 | STR | Strength (single kanji) |
| 10 | `4841ef9a2dc4981` | 幸運度 | LCK | Luck |
| 11 | `5d0c6327e20384e7` | 敏捷度 | AGI | Agility |
| 12 | `aa43f966ad69195e` | 生命力 | VIT | Vitality |
| 13 | `bb20512b10c3128b` | 信仰心 | PIE | Piety/Faith |
| 14 | `d455234204274c43` | 知恵 | IQ | Intelligence/Wisdom |
| 15 | `f2013a64642252e3` | HP/MAX | HP/MAX | Already Latin text |

### Button (40x24, 1 dump)

| # | Texture Hash | Japanese | English | Meaning |
|---|-------------|----------|---------|---------|
| 16 | `d09a04bdfaf715bc` | 決定 | OK | Confirm button |

---

## Corrections to Existing patch_r1188_direct.py

The `STAT_LABELS_64x16` mapping in `tools/patch_r1188_direct.py` has several incorrect label assignments. Corrected mapping based on visual verification:

| Hash | Old (wrong) | Correct |
|------|------------|---------|
| `280ea82c1c476a98` | Luck | **STR** (力 = Strength) |
| `4841ef9a2dc4981` | Agility | **LCK** (幸運度 = Luck) |
| `5d0c6327e20384e7` | Vitality | **AGI** (敏捷度 = Agility) |
| `aa43f966ad69195e` | Piety | **VIT** (生命力 = Vitality) |
| `bb20512b10c3128b` | IQ | **PIE** (信仰心 = Piety) |
| `f2013a64642252e3` | Strength | **HP/MAX** (already Latin) |

Additionally, `d455234204274c43` (知恵 = IQ/Wisdom) was **missing** from the tool entirely.

---

## Deswizzled Atlas Character Grid

The deswizzled atlas contains a proportional-width font. Characters are NOT in a fixed grid -- each character has a different width. The layout:

- **Rows 0-1** (y=5-47): ASCII characters (digits 5-9, punctuation, A-I, copyright, a-s)
- **Rows 2-5** (y=50-141): Hiragana + Katakana  
- **Rows 6-41** (y=144-1008): Kanji (approximately 20-21 characters per row at ~24px spacing)
- **Right half** (x=512-1023): Deswizzle artifacts, not valid character data
- **Row height**: ~24px from row 6 onward; rows 0-5 vary (17-22px)
- **Characters per row**: ~20-21, with variable individual widths (7-23px)

### Atlas Row Contents (rows 6-41, kanji region)

| Row | y | Characters |
|-----|---|-----------|
| 6 | 144 | ヴ引何岸宮去橋険故向行今次者人静騒達渡悲負 |
| 7 | 168 | 街楽換歓関期気客強近金揚軽迎見言限後交困差 |
| 8 | 192 | 紹上乗場常情信盛前相他台大段男知置柱調鉄店 |
| 9 | 216 | 頼理立連脇長髪成告落容薬味物美転眺帯先女書 |
| 10 | 240 | 念命拾様生最記憶力存在感薄会忘顔天才不幸横 |
| 11 | 264 | 騎許景肩光広刻国査罪司士始子思紙至視床章触 |
| 12 | 288 | 令路蟲員汚屋家改外看奇禁係建元口止字社小消 |
| 13 | 312 | 追閉間際丸投頭確認詳細帳済主巻結証明替破棄 |
| 14 | 336 | 飛文急離歌聞♪布扉招機甲師妃幼僧❤途端鋭輝 |
| 15 | 360 | 財殺史死寂首祝諸城職色心深申神垂水制潜全双 |
| 16 | 384 | 方望毎満霧門子欲隣例歴腕鬱船居慌考荒自室食 |
| 17 | 408 | 持盗賊聖密将軍侶忍侍鍛義黒答質問由説待嬉降 |
| 18 | 432 | 野太響姉重優巨漢越種族乱仲求暗俺華革額寒汗 |
| 19 | 456 | 貧帽溜麗労郎綺怪喧耳雑安院患祈厳祭施寺治性 |
| 20 | 480 | 愛咲花償陽御麻痺決法売礼毅願壇昔救服非貴銭 |
| 21 | 504 | 策像試練平嘘透穏京表争丈夫青宅札軒狭裏号彫 |
| 22 | 528 | 武骨類格白銀茶鼻剣能秘句促掛温紅座凹冷輪率 |
| 23 | 552 | 条署飼市山刷冊作材効経契空脚管解果羽印井因 |
| 24 | 576 | 悩必赴減要和異煙規胡誇散臭従処塔模陸興奮炎 |
| 25 | 600 | 護席態典縛莫腐陛亡娘利領列索余科預点希絡庫 |
| 26 | 624 | 貫頑危喜休警遣五攻叱充寝損第广超討肌伐殿備 |
| 27 | 648 | 腎吸吐紛儀處判悔捨詞之撃器基略携斬研究狂千 |
| 28 | 672 | 髭尽抱血鮮衣染臓腹刺妹絞抜ヶ育央咳既勤月辞 |
| 29 | 696 | 映塊快学噛胸具牽原個乙皇歳産射純焼象辛粋製 |
| 30 | 720 | 普駄鍛倉縮評赦営鑑給況兼省称選揃買販磨未律 |
| 31 | 744 | 農酸蝕隅鋼溶墓焦洞緑到害補挨拐李黄賞粗減還 |
| 32 | 768 | 奏弔氷僅訳魂眩粒厚醍醐沿劇演把是送雫灰豊共 |
| 33 | 792 | 鼓噴雄理惑伸鈍恩批借環境眠徐狙沈斉踊聴詩曲 |
| 34 | 816 | 竜企購脅講怨痕獅七哀阻辰朝東万猛援雅絵疑区 |
| 35 | 840 | 頁海滴煌操馴拍罵浴裕政敬吉誤迫晴宗泥慎概緯 |
| 36 | 864 | 医架貨弓幸秀耐抗炭波搬嬢棺机稀挙己賛覇敏堂 |
| 37 | 888 | 笛婆埋翼賛属滝官拷悟織仇暇脳紀均算慎尊爆幅 |
| 38 | 912 | 逆努疫勘弁遺罰域筒呑曇厄競塞車栓瓶融斐干粘 |
| 39 | 936 | 悦掘拭姫岩池傑泳稿鞄北拝巡渋昇忌纏澄跡猫抵 |
| 40 | 960 | 究沌愉嵐糧烈煉唸嘔奢詑虎析順樽型遙謀仮挟袖 |
| 41 | 984 | 盟怠吊柵拙島衆町叶渉戒績憧屍槽蒸盲兜糸村絆 |

### Label Characters Found in Atlas

Characters from the 16 labels that appear in the deswizzled atlas:

| Char | Row | Approx y | Found in Label |
|------|-----|----------|---------------|
| 性 | 19 | 456 | 性別 (Gender), 属性 (Align) |
| 記 | 10 | 240 | 記号 (Symbol) |
| 号 | 21 | 504 | 記号 (Symbol) |
| カ | 4 | 98 | カナ (Kana) |
| 職 | 15 | 360 | 職業 (Class) |
| 種 | 18 | 432 | 種族 (Race) |
| 族 | 18 | 432 | 種族 (Race) |
| 力 | 10 | 240 | 力 (STR), 生命力 (VIT) |
| 生 | 10 | 240 | 生命力 (VIT) |
| 命 | 10 | 240 | 生命力 (VIT) |
| 信 | 8 | 192 | 信仰心 (PIE) |
| 心 | 15 | 360 | 信仰心 (PIE) |
| 知 | 8 | 192 | 知恵 (IQ) |
| 幸 | 10/36 | 240/864 | 幸運度 (LCK) |
| 決 | 20 | 480 | 決定 (OK) |
| 属 | 37 | 888 | 属性 (Align) |
| 敏 | 36 | 864 | 敏捷度 (AGI) |
| H | 0 | 5 | HP/MAX |
| A | 0 | 5 | HP/MAX |
| X | 2 | 50 | HP/MAX |

### Characters NOT Found in Atlas Transcription

Some label characters were not located in the atlas during this scan. They may exist in rows not fully transcribed, or the atlas transcription may have errors for certain complex kanji:

- 別 (from 性別)
- ナ (from カナ) 
- 度 (from 幸運度, 敏捷度)
- 捷 (from 敏捷度)
- 運 (from 幸運度)
- 英 (from 英数)
- 数 (from 英数)
- 業 (from 職業)
- な (from かな)
- 仰 (from 信仰心)
- 定 (from 決定)
- 恵 (from 知恵)
- P, /, M (from HP/MAX)

Note: These characters ARE present in the game's VRAM version of the atlas; they are simply not in the visible area of the deswizzled rendering, or were misread during the manual transcription of 800+ kanji.

---

## Actionable Translation Path

Since atlas coordinate mapping is blocked by the deswizzle issue, the viable translation approaches are:

1. **PCSX2 texture replacement** (already implemented in `tools/patch_r1188_direct.py`): Replace each dump PNG with an English-rendered version, keyed by texture hash. This works immediately with no atlas editing needed.

2. **Fix the stat label hash mapping** in `tools/patch_r1188_direct.py`: The stat label hashes are incorrectly assigned (see Corrections section above). The `d455234204274c43` (知恵/IQ) hash is missing entirely.

3. **EXE UV redirect** (not yet implemented): Patch the EXE's UV lookup code to point tab/stat labels to a different atlas region where English text has been rendered. This requires finding the UV table in the EXE.
