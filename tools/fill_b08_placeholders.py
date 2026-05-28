import json

path = "C:/Programmieren/wizardrytranslation/data/type2_translated/batch_08.json"
with open(path, encoding="utf-8") as f:
    data = json.load(f)

# Build lookup by (resource, msg_index)
idx_map = {}
for i, e in enumerate(data):
    idx_map[(e["resource"], e["msg_index"])] = i

translations = {
    (1212, 67): "You fought off the / swarming creatures / and now stand / before me.",
    (1212, 78): "Gather every last / ounce of courage.",
    (1212, 88): "Even if you forget / the silenced ones, / they will return / as long as you / remember the source.",
    (1212, 92): "Received the key / to the floor.",
    (1212, 96): "The floor has / returned!!",
    (1212, 97): "So this is what / it means!!",
    (1212, 101): "To fulfill / a wish!",
    (1212, 122): "Lucy noticed and / came over from / behind the counter.",
    (1212, 131): "Lucy pulled a / secret scroll from / her bag and / read it aloud.",
    (1212, 153): "Really? You sure? / You don't have to / worry about it!",
    (1212, 155): "Really? You sure? / You don't have to / worry about it!",
    (1212, 165): "Whaaaat?! You / don't have 5000g?! / That's rough, pal!",
    (1212, 168): "Really? You sure? / You don't have to / worry about it!",
    (1212, 170): "Really? You sure? / You don't have to / worry about it!",
    (1212, 185): "A joyful cry can / be heard from / somewhere.",
    (1212, 221): "Good you were / prepared. Forgetting / monsters makes you / the real monster.",
    (1212, 259): "Has strong / vitality.",
    (1212, 260): "Push further and / you could gain / incredibly strong / abilities.",
    (1212, 261): "Sharp vision. / Concentration / seems high too.",
    (1212, 278): "Without battle / sense, even with / good gear, you / can't draw out / true power.",
    (1212, 280): "Preparation is / still lacking, but / soon you can draw / out spells even / in tough fights.",
    (1212, 294): "Oh no! It broke.",
    (1212, 358): "Only 1 bracelet, / so if there are / multiple winners, / prize changes to / the next item.",
    (1212, 443): "I deal in fine / art. I make my / living viewing / sealed portraits.",
    (1212, 444): "You don't seem to / have any medals / of achievement.",
    (1212, 446): "Paid the fee / of 1000g.",
    (1212, 533): "What the hell / are you saying?!",
    (1212, 538): "If you wanna beat / the witch so bad, / do it yourself!",
    (1212, 539): "Yeah, if only / I could.",
    (1212, 556): "What if we die, / then what?",
    (1212, 610): "I made it here, / but I've no wish / to defeat Aurora / or to return / alive.",
    (1212, 680): "Erika waved her / hand as if to / brush something away.",
    (1212, 698): "Never seen such / a cowardly sight!",
    (1213, 8): "Defeat the / creatures and / return to this / place once more.",
}

count = 0
for (res, mi), eng in translations.items():
    key = (res, mi)
    if key in idx_map:
        i = idx_map[key]
        data[i]["english"] = eng
        count += 1
        print(f"  R{res}[{mi}]: {eng[:60]}")
    else:
        print(f"  WARNING: R{res}[{mi}] not found!")

with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\nFilled {count} entries.")
