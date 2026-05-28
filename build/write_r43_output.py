import json
inferred = {
    "resource": "0043_type01.bin",
    "description": "Bar Luna Light - Trap Game and Medal Exchange dialogue",
    "inferred_glyphs": {},
    "uncertain_glyphs": {},
    "context_notes": {}
}
g = inferred["inferred_glyphs"]
g["0"] = {"char": " ", "confidence": "LOW", "evidence": "Separator/padding in msg 67 (hai) and msg 72"}
g["8"] = {"char": "\uff08", "confidence": "MEDIUM", "evidence": "Opening bracket in msg 71 template"}
g["9"] = {"char": "\uff09", "confidence": "MEDIUM", "evidence": "Closing bracket in msg 71 template"}
g["16"] = {"char": "\uff10", "confidence": "HIGH", "evidence": "Number 0 in 500G price. Consistent with 18=2"}
g["17"] = {"char": "\uff11", "confidence": "HIGH", "evidence": "Number 1 in msg 31 and 71"}
g["21"] = {"char": "\uff15", "confidence": "HIGH", "evidence": "Number 5 in 500G price"}
g["39"] = {"char": "\uff27", "confidence": "HIGH", "evidence": "G for Gold in price display"}
g["107"] = {"char": "\u679a", "confidence": "MEDIUM", "evidence": "Counter for flat objects in medal display"}
g["193"] = {"char": "\u30a2", "confidence": "HIGH", "evidence": "Katakana A in aitemu=item (msg 35)"}
g["194"] = {"char": "\u30a4", "confidence": "HIGH", "evidence": "Katakana I in aitemu and purei (msg 35,71)"}
g["211"] = {"char": "\u30c6", "confidence": "HIGH", "evidence": "Katakana TE in aitemu (msg 35)"}
g["225"] = {"char": "\u30e0", "confidence": "HIGH", "evidence": "Katakana MU in ge-mu=game and aitemu"}
g["233"] = {"char": "\u30eb", "confidence": "HIGH", "evidence": "Katakana RU in medaru=medal"}
g["234"] = {"char": "\u30ec", "confidence": "HIGH", "evidence": "Katakana RE in purei=play (msg 71)"}
g["242"] = {"char": "\u30b2", "confidence": "HIGH", "evidence": "Katakana GE in ge-mu=game"}
g["261"] = {"char": "\u30d7", "confidence": "HIGH", "evidence": "Katakana PU in purei=play (msg 71)"}
g["308"] = {"char": "\u4fe1", "confidence": "HIGH", "evidence": "shin in jishin=confidence (msg 28)"}
g["338"] = {"char": "\u4e00", "confidence": "HIGH", "evidence": "ichi in ippai=one cup (msg 5)"}
g["339"] = {"char": "\u6c17", "confidence": "HIGH", "evidence": "ki in kibun tenkan=change of pace (msg 16)"}
g["379"] = {"char": "\u8ee2", "confidence": "HIGH", "evidence": "ten in kibun tenkan (msg 16)"}
g["396"] = {"char": "\u6570", "confidence": "MEDIUM", "evidence": "kazo in kazoeru=count (msg 15)"}
g["398"] = {"char": "\u5e30", "confidence": "HIGH", "evidence": "kae in kaeru=return (msg 20)"}
g["415"] = {"char": "\u56de", "confidence": "HIGH", "evidence": "kai=round in 1kai 500G (msg 31)"}
g["419"] = {"char": "\u91d1", "confidence": "HIGH", "evidence": "kane=money (msg 43,75)"}
g["496"] = {"char": "\u6240", "confidence": "HIGH", "evidence": "sho in shoji=possession (msg 75,77,86)"}
g["510"] = {"char": "\u5ba2", "confidence": "HIGH", "evidence": "kyaku=customer (msg 13: okyaku-san)"}
g["529"] = {"char": "\u4ea4", "confidence": "HIGH", "evidence": "kou in koukan=exchange (msg 35,56,74,82)"}
g["531"] = {"char": "\u96c6", "confidence": "HIGH", "evidence": "atsu in atsumeru=collect (msg 34)"}
g["552"] = {"char": "\u5206", "confidence": "HIGH", "evidence": "bun in kibun=mood (msg 16)"}
g["562"] = {"char": "\u81ea", "confidence": "HIGH", "evidence": "ji in jishin=confidence (msg 28)"}
g["572"] = {"char": "\u4f55", "confidence": "HIGH", "evidence": "nani in nanika=something (msg 10)"}
g["581"] = {"char": "\u7269", "confidence": "HIGH", "evidence": "mono in mochimono=belongings (msg 64)"}
g["587"] = {"char": "\u7406", "confidence": "HIGH", "evidence": "ri in seiri=organize (msg 64)"}
g["603"] = {"char": "\u54c1", "confidence": "HIGH", "evidence": "hin in keihin=prize and shojihin (msg 52,86)"}
g["619"] = {"char": "\u7fd2", "confidence": "HIGH", "evidence": "shuu in renshuu=practice (msg 29,38,69)"}
g["634"] = {"char": "\u6765", "confidence": "HIGH", "evidence": "ki in kuru=come (msg 65)"}
g["635"] = {"char": "\u983c", "confidence": "HIGH", "evidence": "rai in irai=request (msg 2,10,14)"}
g["656"] = {"char": "\u8ab0", "confidence": "HIGH", "evidence": "dare=who (msg 58)"}
g["665"] = {"char": "\u640d", "confidence": "MEDIUM", "evidence": "son in sonsuru=to lose (msg 37)"}
g["668"] = {"char": "\u6301", "confidence": "HIGH", "evidence": "mo in motsu=hold (msg 58,64,75,77,86)"}
g["709"] = {"char": "\u5fc5", "confidence": "HIGH", "evidence": "hitsu in hitsuyou=required (msg 78)"}
g["710"] = {"char": "\u8981", "confidence": "HIGH", "evidence": "you in hitsuyou=required (msg 78)"}
g["712"] = {"char": "\u8db3", "confidence": "HIGH", "evidence": "ta in tariru=sufficient (msg 43,81,83)"}
g["786"] = {"char": "\u4f9d", "confidence": "HIGH", "evidence": "i in irai=request (msg 2,10,14)"}
g["855"] = {"char": "\u63db", "confidence": "HIGH", "evidence": "kan in koukan=exchange and tenkan (msg 16,35,56,74,82)"}
g["876"] = {"char": "\u59cb", "confidence": "HIGH", "evidence": "haji in hajimeru=begin (msg 40)"}
g["892"] = {"char": "\u52d9", "confidence": "MEDIUM", "evidence": "mu in ninmu=mission (msg 85)"}
g["898"] = {"char": "\u676f", "confidence": "HIGH", "evidence": "hai in ippai=one cup (msg 5)"}
g["901"] = {"char": "\u5f15", "confidence": "HIGH", "evidence": "hi in hikiukeru=accept (msg 11)"}
g["902"] = {"char": "\u53d7", "confidence": "HIGH", "evidence": "u in ukeru=receive (msg 11,80)"}
g["906"] = {"char": "\u7df4", "confidence": "HIGH", "evidence": "ren in renshuu=practice (msg 29,38,69)"}
g["908"] = {"char": "\u6b8b", "confidence": "HIGH", "evidence": "zan in zannen=too bad (msg 46)"}
g["909"] = {"char": "\u5ff5", "confidence": "HIGH", "evidence": "nen in zannen=too bad (msg 46)"}
g["910"] = {"char": "\u666f", "confidence": "HIGH", "evidence": "kei in keihin=prize (msg 52,55,73)"}
g["911"] = {"char": "\u6574", "confidence": "HIGH", "evidence": "sei in seiri=organize (msg 64)"}
g["944"] = {"char": "\u53d6", "confidence": "HIGH", "evidence": "to in uketoru=receive (msg 80)"}
g["999"] = {"char": "\u4efb", "confidence": "MEDIUM", "evidence": "nin in ninmu=mission (msg 85)"}
inferred["context_notes"] = {
    "resource_purpose": "Bar Luna Light tavern UI - trap game, medal exchange, quest list",
    "speaker": "Gin Barbus (barkeep), casual male Japanese",
    "guide_reference": "BAR LUNA LIGHT, TRAP GAME, MEDAL EXCHANGE sections"
}
with open("C:/Programmieren/wizardrytranslation/data/inferred_r43.json", "w", encoding="utf-8") as f:
    json.dump(inferred, f, ensure_ascii=False, indent=2)
total = len(g)
high = sum(1 for v in g.values() if v["confidence"] == "HIGH")
medium = sum(1 for v in g.values() if v["confidence"] == "MEDIUM")
low = sum(1 for v in g.values() if v["confidence"] == "LOW")
print(f"Written {total} inferred glyphs ({high} HIGH, {medium} MEDIUM, {low} LOW)")
