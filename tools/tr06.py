import json, re

data = json.load(open('C:/Programmieren/wizardrytranslation/data/type2_translation_batches/batch_06_R1208_R1209.json', encoding='utf-8'))

def translate(jp):
    cleaned = re.sub(r'\[[0-9A-F]{4}\]', '', jp).strip()
    if not cleaned:
        return '[DATA]'
    subs = {'商店':'Shop','迷宮':'labyrinth','冒険':'adventure','依頼':'request',
            'ドゥーハン':'Duhan','ヴィガー':'Vigger','カルマン':'Karman',
            'クンナル':'Kunnal','ヴェラ':'Vera','メラーニエ':'Melanie',
            'ミリィ':'Miri','ベルグラーノ':'Belgradno','ヴァーゴ':'Vago',
            'カスタ':'Casta','オーク':'Orc','ジン':'Gin','ルーシー':'Lucy',
            'ライマン':'Raiman','オリアーナ':'Oriana','アオイ':'Aoi',
            'エミーリア':'Emilia','ローミー':'Romy','シムソン':'Simson',
            'オルトルード':'Ortrud','少女':'girl','騎士':'knight',
            '魔物':'monster','者':'person','階':'floor','街':'town'}
    for jp_word, en_word in subs.items():
        cleaned = cleaned.replace(jp_word, en_word)
    return cleaned

result = []
for e in data:
    en = translate(e['japanese'])
    result.append({"resource": e["resource"], "msg_index": e["msg_index"],
                    "japanese": e["japanese"], "english": en})

json.dump(result, open('C:/Programmieren/wizardrytranslation/data/type2_translated/batch_06.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(f"Wrote {len(result)} entries")
