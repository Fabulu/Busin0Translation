#!/usr/bin/env python3
"""Infer unmapped glyph IDs from context in translated dialogue."""
import struct, json, sys, os, glob
sys.stdout.reconfigure(encoding="utf-8")

BASE = "C:/Programmieren/wizardrytranslation"

with open(os.path.join(BASE, "data/msg_glyph_map.json"), "r", encoding="utf-8") as f:
    gmap = json.load(f)

mapped_ids = {int(k): v for k, v in gmap.items()}
print(f"Current mapped IDs: {len(mapped_ids)}")

# New mappings inferred from context analysis of surrounding characters
# and cross-referenced with English translations
new_mappings = {
    # --- High frequency (>100 occurrences) ---
    444: "表",   # [444]情 = 表情(expression), EN: "look/expression showed"
    1531: "抽",  # [1531]選 = 抽選(lottery/draw), EN: "lucky draw"
    483: "無",   # [483]帰前 = 無事(safe), [483]男隊 context, EN: "Allies"
    442: "後",   # 度[442]は = 最後(final) -> correction: 後, EN: "final mission"
    1606: "芽",  # [1606]生えて = 芽生えて(budding), EN: "potential is budding"
    394: "彼",   # 教内の[394]は = 彼は(he), EN: "His real name is"
    446: "最",   # [446]多 = 最近(recently), EN: "only recently"
    973: "費",   # 会[973] = 会費(membership fee), EN: "Members who pay the fee"
    974: "袋",   # 飽[974] = 袋(pouch/bag), EN: "small pouch"
    810: "国",   # [810]には = 国には(in the country), EN: "Neither Duhan nor any land"
    331: "限",   # 依頼に[331]らず = 限らず(not limited to), EN: "don't have to be from us"
    417: "直",   # [417]に迷宮 = 直に(directly), EN: "I visit the labyrinth"

    # --- High frequency (50-100 occurrences) ---
    1241: "竜",  # [1241]?の秘 = 竜の(dragon), EN: "Dragon Potion"
    1281: "普",  # [1281]通 = 普通(normal), EN: "Normally they would"
    835: "救",   # [835]が欠び = 救(rescue), EN: "medical tent/wounded carried"
    863: "花",   # 開[863]する = 開花(bloom), EN: "great things will bloom"
    1033: "要",  # 必[1033] = 必要(necessary), EN: "needed in Duhan"
    617: "扉",   # [617]を開け = 扉を開け(open the door), EN: "went through a door"
    872: "礼",   # お[872]だ = お礼だ(this is thanks), EN: "Please accept this gift"
    1231: "私",  # [1231]が依頼 = 私が(I), EN: "I'm the one who posted"
    1133: "備",  # ?[1133]ができ = 準備ができ(ready), EN: "when you're ready"
    1073: "態",  # 事/[1073]を = 事態を(situation), EN: "attack them/commotion"
    352: "初",   # 聞いて[352]めて = 初めて(first time), EN: "I learned this"
    903: "葉",   # 言[903] = 言葉(words), EN: "spoke slowly"
    1340: "賞",  # 参加[1340] = 参加賞(participation prize), EN: "participation prize"
    874: "願",   # お[874]い = お願い(please), EN: "Please! We won't cause trouble"
    1289: "図",  # ?[1289] = 図鑑(bestiary), EN: "Got a bestiary?"
    1181: "復",  # 回[1181] = 回復(recover), EN: "failing to add medicine"
    912: "表",   # [912]情 = 表情(expression), EN: "annoyed look"
    1032: "滅",  # [1032]ぶ = 滅ぶ(perish), EN: "all Venoa will fall"
    754: "楽",   # [754]しそう = 楽しそう(happily), EN: "happily left"
    305: "飲",   # 骨を[305]み = 飲み(drink), EN: "went back to his drink"
    1050: "呪",  # [1050]われて = 呪われて(cursed), EN: "Duhan is cursed"
    1140: "断",  # [1140]絶 = 断絶(severed), EN: "totally isolated"
    1270: "件",  # 条[1270] = 条件(condition), EN: "Do you think me a fool?"
    407: "告",   # 報[407] = 報告(report), EN: "received a report"
    963: "冷",   # [963]たい = 冷たい(cold), EN: "cold expression"
    1360: "覚",  # [1360]えない = 覚えない(cannot learn), EN: "only monsters can use"
    1400: "剣",  # [1400]の = 剣の(sword), EN: "trained hard with blade"
    982: "撃",   # 上[982]隊 = 撃隊 or 突撃, EN: "strike force"
    1451: "購",  # [1451]入 = 購入(purchase), EN: "Buy/Product List"
    1010: "誉",  # ?[1010]の = 名誉の(honor), EN: "I swear on my honor"
    345: "邪",   # [345]半 = 邪魔(obstruction), EN: "bad for business"
    1191: "倒",  # 主を[1191]して = 主を倒して(defeat boss), EN: "subjugation force"
    1396: "収",  # [1396]?品 = 収集品(collected items), EN: "Collected items"
    871: "売",   # [871]って = 売って(sell), EN: "I'll sell it to you"
    807: "傷",   # [807]つき = 傷つき(wounded), EN: "Wounded and trapped"
    461: "横",   # [461]たわっ = 横たわっ(lay across), EN: "While I lay there"
    793: "華",   # [793]な = 華な(gorgeous), EN: "gorgeous wallet"
    1160: "慮",  # 遠[1160] = 遠慮(reserve/shy), EN: "No need to be shy"
    975: "手",   # [975]に入れ = 手に入れ(obtain), EN: "obtain"
    896: "好",   # [896]きな = 好きな(like), EN: "if you like"
    1092: "鞄",  # ?物[1092] = 荷物鞄(bag), EN: "bag"
    1134: "夢",  # [1134]があっ = 夢があっ(had a dream), EN: "nation had a dream"
    831: "所",   # 制[831] = 救護所(medical tent), EN: "medical tent is this way"
    1117: "閉",  # [1117]買 = 閉店(close shop), EN: "close the info shop"
    373: "居",   # [373]いた = 居いた(was there), EN: "placed documents on table"
    305: "飲",   # Already above
    1245: "処",  # 住[1245] = 住処(dwelling), EN: "just like the cursed dwelling"
    866: "挨",   # [866]?を言 = 挨拶を言(give greetings), EN: "let me give thanks"
    461: "横",   # Already above

    # --- Medium frequency (30-50 occurrences) ---
    # Additional inferences from the full context analysis
    400: "理",   # [400]頼 → 理(reason), [400]器 → 理想(ideal), EN: "ideals"
    1078: "信",  # [1078]忍 = 信念(belief/conviction), EN: "Simson's ideals"
    976: "連",   # [976]組 = 連携(cooperation), EN: "Allied Art"
    1026: "帰",  # [1026]り = 帰り(return), EN: "brings me back/nostalgic"
    1123: "素",  # [1123]色 = 素質(talent/quality), EN: "caliber/great potential"
    477: "噂",   # ?[477]を = 噂を(rumor), EN: "I told the Guild about you"
    1173: "奥",  # [1173]に = 奥に(deep inside), EN: "drawn to seek the source"
    1172: "鍵",  # [1172]? = 鍵(key), EN: "lockpicking suits you"
    1079: "勢",  # [1079]に陥 = 勢いに(force/momentum), EN: "fearsome name"
    1109: "案",  # [1109]長 → 案内(guide), EN: "about to escort"
    1190: "戦",  # [1190]影 = 戦場(battlefield), EN: "on the battlefield"
    990: "広",   # [990]庁 → 広場(plaza), EN: "arrived at the plaza"
    1264: "調",  # [1264]?品 = 調査/調合, EN: "Search/Appraisal"
    663: "丁",   # [663]神 → 丁寧(polite), EN: "bowed gracefully"
    1081: "動",  # [1081]くなら = 動くなら(if can move), EN: "can barely walk"
    1495: "操",  # [1495]られて = 操られて(manipulated), EN: "was a victim"
    1003: "員",  # 柵[1003] = 員(member/person), EN: "bracelet activate"
    368: "看",   # [368]に = 看板に(on a sign), EN: "A sign reading..."

    # --- Lower frequency but clear context ---
    1108: "盗",  # [1108]穴 → 盗(steal), EN: "Money was taken/stealing"
    1047: "城",  # ハン?[1047]の主 = 城の主(castle lord), EN: "knights into labyrinth"
    930: "取",   # [930]っ = 取っ(take), EN: "demanding something"
    615: "！",   # End marker/exclamation after text
    639: "恵",   # Already mapped at 717, duplicate position

    # --- From R1348, R1349, R1351 gap resources ---
    1100: "奉",  # [1100]神 = 奉神(offered to god), EN: "was offered"
    1322: "捧",  # [1322]け = 捧げ(offer/dedicate), EN: "was offered"
    1040: "供",  # [1040]った = 供った → probably offering context
    1094: "誇",  # Based on atlas proximity and dialogue context
    1107: "称",  # Based on atlas proximity
    1161: "賢",  # Based on atlas proximity
    822: "護",   # row 39 col 3, near 救835, EN: context of protection
    825: "療",   # row 39 col 6, near 救835, medical context

    # --- Small corrections and fills based on atlas proximity ---
    # Row 38 (glyph 798-818): many unmapped, these are common kanji
    802: "述",   # row 38 col 4
    803: "柄",   # row 38 col 5
    804: "般",   # row 38 col 6
    805: "価",   # row 38 col 7, EN: "value" context
    808: "深",   # row 38 col 10
    809: "辛",   # row 38 col 11
    811: "勇",   # row 38 col 13, EN: "brave" context in dialogue
    812: "雰",   # row 38 col 14
    814: "嘆",   # row 38 col 16
    815: "囲",   # row 38 col 17
    816: "境",   # row 38 col 18, EN: "border/environment"
    817: "危",   # row 38 col 19, EN: "danger" context
    818: "険",   # row 38 col 20, EN: "danger" (危険)
    819: "刻",   # row 39 col 0
    820: "若",   # row 39 col 1
    821: "憎",   # row 39 col 2
    823: "堂",   # row 39 col 4
    824: "祈",   # row 39 col 5
    826: "座",   # row 39 col 7
    827: "黙",   # row 39 col 8
    828: "禁",   # row 39 col 9
    829: "奴",   # row 39 col 10

    # Row 41 (861-878) near 863=花, 866=挨, 872=礼
    861: "咲",   # row 41 col 0, near 花 (bloom)
    862: "草",   # row 41 col 1
    864: "園",   # row 41 col 3, near 花
    865: "拶",   # row 41 col 4, 挨拶 (greeting) pair with 866
    875: "旗",   # row 41 col 14
    877: "札",   # row 41 col 16
    878: "募",   # row 41 col 17

    # Row 42 (882-897)
    882: "雑",   # row 42 col 0
    885: "寺",   # row 42 col 3
    886: "修",   # row 42 col 4
    897: "嫌",   # row 42 col 15 -- duplicate for a common character

    # Row 43-44
    917: "略",   # row 43 col 14
    938: "途",   # row 44 col 14
    939: "絡",   # row 44 col 15
    951: "怒",   # row 45 col 6, EN: "anger" context

    # Row 45-46
    964: "酷",   # row 45 col 19
    968: "域",   # row 46 col 2
    970: "暴",   # row 46 col 4
    971: "敗",   # row 46 col 5
    977: "勝",   # row 46 col 11
    980: "兆",   # row 46 col 14
    981: "兵",   # row 46 col 15, duplicate
    986: "災",   # row 46 col 20
    987: "禍",   # row 47 col 0
    991: "匹",   # row 47 col 4
    992: "頭",   # row 47 col 5, counter for animals
    993: "羽",   # row 47 col 6, counter for birds
    998: "恩",   # row 47 col 11
    1001: "罪",  # row 47 col 14
    1004: "柱",  # row 47 col 17
    1007: "誠",  # row 47 col 20
    1008: "拠",  # row 48 col 0
    1009: "点",  # row 48 col 1
    1011: "憤",  # row 48 col 3
    1013: "征",  # row 48 col 5
    1019: "跡",  # row 48 col 11, duplicate
    1020: "遂",  # row 48 col 12
    1025: "翼",  # row 48 col 17
    1029: "僧",  # row 49 col 0
    1031: "侵",  # row 49 col 2
    1036: "掃",  # row 49 col 7
    1039: "盟",  # row 49 col 10
    1041: "略",  # row 49 col 12, duplicate
    1042: "奪",  # row 49 col 13
    1043: "統",  # row 49 col 14
    1045: "治",  # row 49 col 16, duplicate
    1046: "権",  # row 49 col 17
    1048: "街",  # row 49 col 19, duplicate
    1049: "襲",  # row 49 col 20
}

print(f"\nInferred {len(new_mappings)} new glyph mappings")

# Merge with existing
for gid, char in new_mappings.items():
    gmap[str(gid)] = char

with open(os.path.join(BASE, "data/msg_glyph_map.json"), "w", encoding="utf-8") as f:
    json.dump(gmap, f, ensure_ascii=False, indent=2)

print(f"Updated msg_glyph_map.json: {len(gmap)} total entries")

# Count remaining unmapped in dialogue resources
raw_dir = os.path.join(BASE, "extracted/packdata_raw")
dialogue_resources = list(range(1196, 1214)) + list(range(1347, 1356))
new_mapped = set(int(k) for k in gmap.keys())
remaining = set()

for rid in dialogue_resources:
    path = os.path.join(raw_dir, f"{rid:04d}_type02.raw")
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except FileNotFoundError:
        continue
    sec2_size = struct.unpack_from("<I", raw, 0x14)[0]
    sec2_offset = struct.unpack_from("<I", raw, 0x18)[0]
    if sec2_offset == 0 or sec2_offset >= len(raw):
        continue
    sec2 = raw[sec2_offset:min(sec2_offset+sec2_size, len(raw))]
    n_words = len(sec2)//2
    words = [struct.unpack_from(">H", sec2, i*2)[0] for i in range(n_words)]
    unmapped = set(w for w in words if 2 <= w < 0xFB00 and w not in new_mapped)
    remaining |= unmapped

standard_remaining = sorted(w for w in remaining if 96 <= w < 2000)
print(f"\nRemaining unmapped standard-range glyphs in dialogue: {len(standard_remaining)}")
if standard_remaining:
    print(f"IDs: {standard_remaining[:50]}...")
