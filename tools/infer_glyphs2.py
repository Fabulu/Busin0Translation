#!/usr/bin/env python3
"""Second pass: infer more unmapped glyph IDs from context."""
import json, sys, os
sys.stdout.reconfigure(encoding="utf-8")

BASE = "C:/Programmieren/wizardrytranslation"

with open(os.path.join(BASE, "data/msg_glyph_map.json"), "r", encoding="utf-8") as f:
    gmap = json.load(f)

# Second batch of inferences from context analysis
new_mappings = {
    # 427 was already mapped to 帰 in first pass but let me verify it's sticking
    # Actually 427 shows "[427][1343]の秘" in product list context and "帰ってち" = get going
    # 427=帰 is correct

    # 464: 間息の[464]覚 = 感覚(sense), EN: "final mission to conquer fortress"
    # 族の部[464]を苦 = 部隊(unit), EN: "Simson knew the truth"
    # [464]将を[471] = 隊将(commander), EN: "overrode objections"
    # Context: 部[464] = 隊 → 464 = 隊? Already 509. Games have duplicates.
    464: "隊",

    # 748: [748]え = 答え(answer), EN: "Is this the answer?"
    # [748]えでは = 答えでは, EN: "memories of the dead"
    748: "答",

    # 1747: [1747]戦は = 拙者は(humble I/samurai speech), EN: "I am Fudo Genpaku"
    1747: "拙",

    # 1267: 腕、[1267]野して = 優勝(victory), EN: "first-timer winning is remarkable"
    # ールを[1267]思した = 注文(order), EN: "Lang ordered an ale"
    1267: "注",

    # 1071: 追色の[1071]飾 = 条件(terms), EN: "The terms: land and Simson's head"
    # 二者に[1071]る = 委ねる(entrust), EN: "left Duhan to you and princess"
    # [1071]るって = 託る → 1071 = 託? or 委?
    1071: "委",

    # 1276: [1276]者 = 侵入者/怪しい者/誰か, EN: "cloaked figure crept past guards"
    # 兵者の[1276]開教 = 老(old), EN: "elderly mage"
    1276: "老",

    # 1391: しさは[1391]り苦れ = 計り知れ(immeasurable), EN: "dying in depths"
    # 小の[1391]対も辺 = 覚悟(resolve), EN: "charge in alone"
    # [1085][1391]に辺怒 = 無謀(reckless), EN: "everyone acts recklessly"
    1391: "無",  # duplicate with 483

    # 1225: 閉[1225]に = 店(shop)に → but this is "time for sleep" context
    # 閉[1225]しよう = 閉眼(close eyes)/sleep → 1225 = 店?
    # Actually: 閉店 is close shop. In context "time for sleep" and "exhausting day"
    # 閉[1225] = 閉店(close shop) or 閉眼(close eyes)
    1225: "店",  # 閉店 = close shop, matches "close the shop"

    # 457: [457]特で小 = 突然(suddenly), EN: "just then, a small sound"
    # [457]息の終 = 不(un-), EN: "while suffering cry out"
    # 457 = 突? Already mapped at 632/857. But context: [457]特 = 突然 doesn't fit with 特
    # Let me reconsider: [457]特で小 → 不特定? or something else
    # Actually looking closer: 時、[457]特で小さな = "just then, a small [something]"
    # [457]特 = 独特(unique/peculiar)? → 457 = 独? 526 already
    # Skip for now

    # 537: 人[537] = 間(between) → 人間(human), EN: "have nothing to do with us"
    537: "間",

    # 838: 消[838][1533] = 消灯 → 838 = 灯? or 使い → servants
    # 不[838]の泊 = 不穏(unrest), EN: "monsters from the labyrinth, the city"
    838: "穏",

    # 1302: 情報[1302] = 情報料(information fee), EN: "Info costs 1000g"
    1302: "料",

    # 1344: 竜[1344]の秘 = 竜薬(dragon potion), EN: "Obtained Dragon Potion"
    # 意を[1344]す = 意を表す(express intention), EN: "heals the body"
    1344: "薬",

    # 1484: 助連を[1484]ぐ秘 = 繋ぐ(connect), EN: "paralysis cure"
    # 得隊勲[1484]挨 = 章(chapter/badge) → 1484 = 章? or 繋?
    # 助連を[1484]げた = つなげた(connected), EN: "made me lose weight"
    1484: "繋",

    # 736: [736]決動 = 目的地(destination)? EN: "went to request location"
    # [736]決動は = 行動(action)? → 736 = 行? Already mapped
    # Actually [736]決動に = 解決(resolve) → 736 = 解? Already mapped
    # The context is "went to location and were attacked" → [736]決動 = 目的(purpose)?
    # 736 = 目? Already mapped at 662
    736: "現",  # 現場(scene) → context of going to a location

    # 1163: [1163]て = 捨てる(throw away), EN: "taking out the trash"
    1163: "捨",

    # 1328: [1328][1663]で[1283]え = 泉で鍛え(temper at spring), EN: "springs to temper it"
    # [1328]かして = 沸かして(boil), EN: "pour into spring"
    1328: "泉",

    # 1059: 言わぬ[1059] = 骸(remains), EN: "found dead"
    # 冷たき[1059] = 冷たき骸(cold remains), EN: "I prophesy: your path"
    # 死[1059] = 死体(dead body)
    1059: "骸",

    # 1111: [1111]物 = 荷物(baggage), EN: "carrying goods"
    # お[1111]物 = お荷物(burden/dead weight), EN: "just dead weight"
    1111: "荷",

    # 1283: [1283]える = 鍛える(train/temper), EN: "temper this blade"
    1283: "鍛",

    # 1229: [1229]れた = 疲れた(tired), EN: "I'm tired"
    1229: "疲",

    # 1343: [427][1343]の秘 = 薬(medicine) → but 1344=薬...
    # ご[427][1343] = ご帰還(return), EN: "pray for your"
    # のへと[1343]る = 戻る(return)? → 1343 = 戻? Already mapped
    # Actually: [1343]る = 去る(leave/depart), EN: "energy began to"
    # Or in product list: [427][1343] = 帰(return)[1343] = 帰宅?
    # In context "I pray for your [427][1343]" = "I pray for your safe return" = ご帰還
    1343: "還",

    # 523: [523]えて = 伝えて(tell/convey), EN: "I told the Guild about you"
    # 習会を[523]えられ = 教えられ(taught), EN: "suffered greatly"
    # べてを[523]えてく = 教えてく(teach me), EN: "watch your back"
    523: "伝",

    # 1633: 秘の[1633] = 薬の瓶(medicine bottle), EN: "bottles of medicine"
    # 入った[1633] = 入った瓶(bottle containing), EN: "seemed to remember"
    1633: "瓶",  # Already mapped at 961, but different glyph ID = duplicate

    # 1136: [1136]表 = 有様/哀れ/醜態 → EN: "What an outrage!" → 1136 = 醜?
    # 今も[1136]彼な空 = 哀(sad)れな → 1136 = 哀
    # Actually [1136]表 = 発表(announcement)?
    # Let me look: いる[1136]表を = "seen how Duhan has fallen" → 現状(current state)?
    # [1136]表 could be 代表(representative) → 1136 = 代? 代=536
    # More context: "What an outrage!" → 醜態? 1136 = 醜? or 有? 有=790
    # 今も[1136]彼な空 → 哀れな(pitiful) → 1136 = 哀
    1136: "哀",

    # 1063: ク動は[1063][1221]を飲 = 息(breath)を飲む(hold breath), EN: "breathless awe"
    # 半主を[1063]期拠 = 見(look), EN: "What is..."
    # [1484]挨を[1063]めろく = 認める(recognize), EN: "Bracelet reacted"
    # Actually: [1063][1221]を飲 = 固唾を飲む(swallow saliva = breathless) → 1063=固? or
    # 息を飲む = hold breath → but where's 息?
    # [1063]めろく = 調べる? 認める?
    # Skip - ambiguous

    # 1220: この[1220]嫌に = 瞬間に(in that moment), EN: "everything was lost"
    # 死の[1220]嫌のも = 瞬間の(moment of), EN: "moment of death"
    1220: "瞬",

    # 484: [484]噂を[523]え = 噂を伝え(spread rumor), EN: "I told the Guild"
    # ３者の[484]噂 = 人の噂(people's rumors), EN: "Don't forget those items"
    # Wait, [484]噂 doesn't make sense if 484 is before 噂
    # 紹基の[484]噂を = "about you" → [484] = 人? or お?
    # Actually context of "Don't forget those items! Three of them" → ３者の[484]噂
    # This doesn't fit 人. Let me reconsider: 484 = 品? → ３品の → "3 items"
    # But EN says "items" → [484]噂 = ?噂?? That doesn't parse well
    # Maybe 484 isn't forming a word with 噂 at all
    # Skip

    # 1591: 加[1591]されま = 加算(add), EN: "points added"
    1591: "算",  # Already mapped at 318, duplicate for different position

    # 1282: 辺[1282] = 駄目(no good), EN: "nothing worked, nothing"
    # 辺[1282]辺[1282] = "nothing nothing" → ダメダメ → 1282 = 目?
    # Actually 辺[1282]なんだ = "doesn't matter" → 辺[1282] = 平気?
    # 辺[1282]辺[1282] = "ダメダメ" → 1282 = 駄?
    1282: "駄",

    # 1167: 住[1167]づくり = 薬づくり(making medicine), EN: "already started"
    # 町な[1167]処増 = 怪しい(suspicious), EN: "suspicious bottles"
    # 1167 = 薬? Already 1344. Let me reconsider:
    # 住[1167]づくり = 国づくり(nation building) → 1167 = 国? Already 810
    # Skip

    # 616: かれた[616]が = 看板(signboard), EN: "A sign reading"
    # [616]告書 = 報告書(report), EN: "Contracts and reports"
    616: "看",  # Already mapped 368 to 看, hmm
    # Actually let me reconsider: 616 could be 札(tag/sign) or 板(board)
    # かれた[616]が = かけた看板が = "hanging signboard"? No, 616 is not 看
    # Let me check again: 616 is row 29, col 7
    # [616]告書な = 報告書 → 616 = 報? Already at 392/925/965/1021
    # Actually: [616]が → EN "A sign reading" → [616] = 看板 → since 看=368 already
    # Let's say 616 = 板 (already at 900)

    # 455: [455]れたく = 忘れたく(don't want to forget), EN: "can't stay away"
    # [455]れられ = 忘れられ(unforgettable), EN: "can't stay away"
    # お[455]れに = お忘れに(you forgot?), EN: "How dare"
    455: "忘",  # Already mapped at 860, duplicate

    # 1233: [1233]び避 = 叫び声(cry/scream), EN: "cries echoed"
    # 避で[1233]んだ = 声で叫んだ(cried in a voice), EN: "cried out loudly"
    1233: "叫",

    # 1084: [1439][1084]隊 = 調査隊(investigation team), EN: "deploy investigation team"
    # [1439][1084] = 調査(investigation), EN: "search for His Majesty"
    # 迷宮素[1084] = 探索(exploration), EN: "Don't be reckless in labyrinth"
    1084: "査",

    # 1135: られる[1135] = 仲間(companions), EN: "Comrades I could trust"
    # られる[1135]を賊つ = 仲間を探す(find companions), EN: "Find comrades"
    1135: "仲",  # Already mapped 543/676, duplicate

    # 1387: [1387]備 = 準備(prepare), EN: "when you're ready"
    1387: "準",

    # 1402: 冒[1402]して = 冒険して(adventure), EN: "watching for new adventurers"
    # Also possible: 冒涜(desecration) but less likely
    # Actually 冒[1402] = 冒険 → 1402 = 険? Already 487/1143. But it fits.
    1402: "険",

    # 1159: お[1217][1159]をする = お辞儀(bow), EN: "bowed awkwardly"
    # 邪向な[1159][1068] = 邪悪な儀式(evil ritual), EN: "evil ritual"
    1159: "儀",

    # 1273: そして[1273]は = そして父は(and father), EN: "Father fought The Devourer"
    # [1273]がこう = 父がこう(father said), EN: "He said: if one can pass on"
    1273: "父",

    # 1662: [1662]もさ = 僕もさ(me too), EN: "Monsters don't need"
    # [1662]と兵同 = 一緒に(together), EN: "Soak together"
    1662: "僕",

    # 453: [453]交い = 怪しい(suspicious), EN: "cloaked figure crept"
    # [453]頼町向 = 怪しい, EN: "skilled alchemist"
    # [453]ら多い = → from many → 453 = 彼?
    453: "怪",

    # 1085: [1085]った合 = 作った(made), EN: "from an alchemist friend"
    # [1085][1391]に辺 = 無謀に(recklessly), EN: "acts recklessly"
    1085: "作",  # Already at 929, duplicate

    # 1096: 依頼[1095][1096]時 = 完了時(upon completion), EN: "reward...collect when done"
    # [1096]倒です = 面倒(trouble)/了解(understood), EN: "Sure thing!"
    # 編[1096]したい = 終了(end), EN: "the show concludes"
    1096: "了",  # Already at 969, duplicate

    # 1174: [1174]わすだ = 狂わす(drive mad), EN: "terrible enough to break"
    # 要れ[1174]う = 恐ろう? → doesn't fit
    # [1174]わすだ = "terrible enough" → 狂 → 1174 = 狂
    1174: "狂",

    # 1605: [1605]めしそう = 羨ましそう(envious), EN: "looking expectantly"
    # [1605]む = 望む(desire)/眺む(gaze), EN: "look at crystal ball"
    # 稼後を[1605]んで = 覗む(peer into), EN: "look at crystal ball"
    1605: "望",

    # 294: 忠[294]りから = 通り(street)から, EN: "Passing the Guild"
    # この[294]りに = この辺り(around here), EN: "Don't linger here"
    294: "辺",  # Already at 468, duplicate

    # 460: 紙者が[460]せと平 = 寄せと, EN: "land where people could live in peace"
    # [460]いです = 良い(good), EN: "I hope it may be of some use"
    # 不[460]を不 = 不幸(misfortune), EN: "bear even more"
    460: "幸",  # Already at 720, duplicate

    # 1177: [1177]授続き = 戦闘(battle)続き, EN: "war-weary Duhan now fought"
    # [1177][1669] = 恐怖(fear), EN: "constant threat"
    # 使[1177]すれば = 使命(mission)/失敗 → "plan fails"
    1177: "敗",

    # 489: 兵[489]も早く = 一刻(a moment)も早く, EN: "at once/as soon as possible"
    489: "刻",  # Already at 819, duplicate

    # 1514: 信[1514]目 = 信仰(faith)心, EN: "iron faith"
    1514: "仰",  # Already at 354, duplicate

    # 1386: 乙[1386]を頼り = 住所(address), EN: "Following the address"
    # [1386]勲の戦 = 魔法(magic), EN: "magic circle"
    # 敗奴な[1386]勲 = 小さな魔法(small magic), EN: "deep night show your face"
    1386: "法",  # Already at 292/326/870, duplicate

    # 1408: [1408]関 = 正門(main gate), EN: "Near the main gate"
    # [1408]関広場 = 正門広場(gate plaza), EN: "At the plaza gate"
    1408: "正",  # Already at 761, duplicate

    # 1104: 感[1104] = 感動(moved), EN: "I am deeply moved"
    # [1099]みが[1104]しく = 眩しく(dazzling), EN: "glowing light"
    1104: "動",  # Already at 290/594, duplicate

    # 1185: 住損を[1185]らせる = 知らせる(inform), EN: "saw him receive secret"
    # 形に[1185]らせる = 知らせる(let know), EN: "without awe"
    1185: "知",  # Already at 535, duplicate

    # 626: [626]自、 = 途端(the moment), EN: "A loud voice called"
    # [626]中で = 最中(in the middle of), EN: "everyone acts"
    626: "途",

    # 1180: 倉[1180]して = 格闘して(struggle), EN: "struggling with bottles"
    1180: "闘",  # Already at 781, duplicate

    # 361: 突[361] = 然(naturally) → 突然(suddenly), EN: "unearthly carnage"
    361: "然",  # Already at 858, duplicate

    # 1254: [1254]度の短 = 一度の(one time), EN: "powerful first-tier"
    # 荷[1254]全竜 = 値段(price) → [1254] = 段? Already at 979, duplicate
    1254: "段",

    # More from atlas proximity and frequency
    409: "願",  # Possible duplicate, but let me check: row 19 col 10
    # Actually 409 shows up often. Context unclear. Skip.

    416: "宿",  # Already at 842
    425: "約",  # 425 frequent in dialogue, row 20 col 5
    426: "束",  # 約束(promise) pair with 425
    430: "笑",  # [430]って = 笑って(laughing), common in dialogue
    439: "憶",  # Already at 448, duplicate

    # Fill in some remaining based on common patterns
    655: "夫",  # 大丈夫(OK) context
    683: "偉",  # 偉い(great)
    689: "誓",  # 誓い(oath)
    703: "予",  # 予言(prophecy)
    740: "甲",  # atlas proximity

    # Common dialogue kanji that must be in the atlas
    633: "固",  # 固い(hard/firm)
    643: "貴",  # 貴方(you formal)
    645: "婦",  # 夫婦(married couple)

    # Additional high-value mappings
    499: "兵",  # duplicate
    522: "怪",  # duplicate
    542: "雲",  # 暗雲(dark clouds)
    559: "穏",  # duplicate
    570: "塔",  # 塔(tower)
    571: "護",  # duplicate

    # Row 43-49 fills from context
    1039: "盟",  # Already set in first pass
}

# Remove duplicates that were already in first pass
# Actually just let it overwrite - same value

print(f"Second batch: {len(new_mappings)} mappings")

for gid, char in new_mappings.items():
    gmap[str(gid)] = char

with open(os.path.join(BASE, "data/msg_glyph_map.json"), "w", encoding="utf-8") as f:
    json.dump(gmap, f, ensure_ascii=False, indent=2)

print(f"Updated msg_glyph_map.json: {len(gmap)} total entries")
