import struct, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
with open("C:/Programmieren/wizardrytranslation/extracted/packdata_resources/0044_type01.bin", "rb") as f:
    data = f.read()
with open("C:/Programmieren/wizardrytranslation/data/msg_glyph_map.json", "r", encoding="utf-8") as f:
    glyph_map = {int(k): v for k, v in json.load(f).items()}
header_end = 234
stream = data[header_end:]
n_vals = len(stream) // 2
vals = struct.unpack(f">{n_vals}H", stream[:n_vals*2])
messages_raw = []
cur = []
for v in vals:
    if v == 0xFFFF:
        if cur:
            messages_raw.append(cur)
        cur = []
    elif v == 0xFFFE:
        pass
    elif v >= 0xFFC0:
        pass
    else:
        cur.append(v)
if cur:
    messages_raw.append(cur)
inferred = {
    668: {"char": "持", "confidence": "HIGH", "reason": "お持ちですか, 所持品, 所持金"},
    920: {"char": "待", "confidence": "HIGH", "reason": "お待ちしておりました"},
    634: {"char": "来", "confidence": "HIGH", "reason": "よく来てくださいました"},
    367: {"char": "行", "confidence": "HIGH", "reason": "変更を行っても, もう行かれるのですか"},
    855: {"char": "更", "confidence": "HIGH", "reason": "変更 (change/modification)"},
    443: {"char": "編", "confidence": "HIGH", "reason": "騎士団を編成する"},
    728: {"char": "成", "confidence": "HIGH", "reason": "編成 (formation)"},
    707: {"char": "選", "confidence": "HIGH", "reason": "選んでください (please select)"},
    708: {"char": "択", "confidence": "HIGH", "reason": "選択してください"},
    927: {"char": "続", "confidence": "HIGH", "reason": "続けますか (will you continue?)"},
    421: {"char": "合", "confidence": "HIGH", "reason": "組み合わせ (combination), 合隊"},
    854: {"char": "組", "confidence": "HIGH", "reason": "組み合わせ"},
    852: {"char": "入", "confidence": "MEDIUM", "reason": "入隊 (enlist), 入りましょう"},
    496: {"char": "所", "confidence": "HIGH", "reason": "所持金, 所持品"},
    419: {"char": "金", "confidence": "HIGH", "reason": "所持金 (money on hand)"},
    603: {"char": "品", "confidence": "HIGH", "reason": "所持品がいっぱいです (inventory full)"},
    712: {"char": "足", "confidence": "HIGH", "reason": "足りません (not enough)"},
    374: {"char": "対", "confidence": "HIGH", "reason": "に対する (regarding)"},
    722: {"char": "獲", "confidence": "HIGH", "reason": "獲得する (acquire)"},
    350: {"char": "得", "confidence": "HIGH", "reason": "獲得 (acquisition)"},
    925: {"char": "報", "confidence": "HIGH", "reason": "報酬 (reward)"},
    926: {"char": "酬", "confidence": "HIGH", "reason": "報酬 (reward)"},
    366: {"char": "影", "confidence": "HIGH", "reason": "影響を与えます (affects)"},
    780: {"char": "響", "confidence": "HIGH", "reason": "影響 (influence)"},
    371: {"char": "与", "confidence": "HIGH", "reason": "与えます (to give)"},
    929: {"char": "作", "confidence": "HIGH", "reason": "作成しますか (will you create?)"},
    621: {"char": "解", "confidence": "HIGH", "reason": "解散 (disband)"},
    351: {"char": "散", "confidence": "HIGH", "reason": "解散 (disband)"},
    931: {"char": "退", "confidence": "HIGH", "reason": "退隊しました (discharged)"},
    431: {"char": "効", "confidence": "HIGH", "reason": "効果 (effect)"},
    511: {"char": "果", "confidence": "HIGH", "reason": "効果 (effect)"},
    693: {"char": "今", "confidence": "MEDIUM", "reason": "今すぐ (right now)"},
    647: {"char": "使", "confidence": "MEDIUM", "reason": "使いますか (will you use?)"},
    913: {"char": "調", "confidence": "MEDIUM", "reason": "調子はどうですか"},
    414: {"char": "子", "confidence": "MEDIUM", "reason": "調子 (condition)"},
    581: {"char": "士", "confidence": "MEDIUM", "reason": "騎士 size variant of 326"},
    500: {"char": "追", "confidence": "MEDIUM", "reason": "追加できるメンバー"},
    501: {"char": "加", "confidence": "MEDIUM", "reason": "追加 (add)"},
    928: {"char": "設", "confidence": "MEDIUM", "reason": "設定する (configure)"},
    497: {"char": "定", "confidence": "MEDIUM", "reason": "設定 (setting)"},
    332: {"char": "装", "confidence": "MEDIUM", "reason": "装備品 (equipment)"},
    602: {"char": "備", "confidence": "MEDIUM", "reason": "装備 (equip)"},
    737: {"char": "決", "confidence": "MEDIUM", "reason": "決して (never)"},
    319: {"char": "何", "confidence": "MEDIUM", "reason": "何かに (something)"},
    669: {"char": "御", "confidence": "MEDIUM", "reason": "御用 (business)"},
    670: {"char": "用", "confidence": "MEDIUM", "reason": "御用 (business)"},
    853: {"char": "勲", "confidence": "LOW", "reason": "くん (merit/medal) as formation resource"},
    338: {"char": "皆", "confidence": "LOW", "reason": "皆無のようです (none available)"},
    898: {"char": "無", "confidence": "LOW", "reason": "皆無 (none at all)"},
}
output = {
    "_metadata": {
        "resource": "0044_type01.bin",
        "resource_index": 44,
        "description": "Knight Order management interface",
        "total_messages": len(messages_raw),
        "total_unknown_glyph_ids": 128,
        "total_inferred": len(inferred),
        "high_confidence": sum(1 for v in inferred.values() if v["confidence"] == "HIGH"),
        "medium_confidence": sum(1 for v in inferred.values() if v["confidence"] == "MEDIUM"),
        "low_confidence": sum(1 for v in inferred.values() if v["confidence"] == "LOW"),
    },
    "inferred_mappings": {str(k): v for k, v in sorted(inferred.items())},
}
with open("C:/Programmieren/wizardrytranslation/data/inferred_r44.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print("Output written to data/inferred_r44.json")
print(f"Total inferred: {len(inferred)} (HIGH: {sum(1 for v in inferred.values() if v['confidence']=='HIGH')}, MED: {sum(1 for v in inferred.values() if v['confidence']=='MEDIUM')}, LOW: {sum(1 for v in inferred.values() if v['confidence']=='LOW')})")
for gid, info in sorted(inferred.items()):
    print(f"  {gid}: {info['char']} ({info['confidence']})")
