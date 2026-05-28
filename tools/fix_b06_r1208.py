import json

INPUT = "C:/Programmieren/wizardrytranslation/data/type2_translated/batch_06.json"

with open(INPUT, "r", encoding="utf-8") as f:
    data = json.load(f)

# Build index of R1208 entries
r1208_idx = {}  # msg_index -> list index in data
for i, e in enumerate(data):
    if e.get("resource") == 1208:
        r1208_idx[e["msg_index"]] = i

# ---- FIX GROUP 1: entries 256-265 (repeats of 254-255) ----
ref_254 = data[r1208_idx[254]]["english"]
ref_255 = data[r1208_idx[255]]["english"]
for mi in range(256, 266):
    if mi in r1208_idx:
        if mi % 2 == 0:
            data[r1208_idx[mi]]["english"] = ref_254
        else:
            data[r1208_idx[mi]]["english"] = ref_255

# ---- FIX GROUP 2: entries 690-710 (repeats of 685-689) ----
refs_685 = [data[r1208_idx[685+j]]["english"] for j in range(5)]
for mi in range(690, 711):
    if mi in r1208_idx:
        offset = (mi - 690) % 5
        data[r1208_idx[mi]]["english"] = refs_685[offset]

# ---- FIX GROUP 3: entries 711-906 (unique story content) ----
translations = {
    # Alchemist encounter
    711: "The alchemist took a / moment to catch his / breath.",
    712: "How was it, did / you recover? Come back / again when you feel ill.",
    713: "You don't have / enough money!",
    714: "What, you don't have / enough money? I'm not / running a charity here.",
    715: "Come back when you / have enough money.",
    716: "I see, you don't / want to. Indeed, peering / into someone's eyes",
    717: "Come back when you / have the time.",
    718: "I study alchemy. / Right now, I'm researching / the ancient Elven",
    719: "The preparations / are not yet complete / and the shop isn't open.",
    720: "Once the preparations / are done, I'll open an / alchemy shop. Come again.",

    # Orc part-time worker
    721: "You met the Orc / working part-time at / the Vigger Shop.",
    722: "The Orc seemed to / remember you too and / came running happily.",
    723: "H-hello~~~ Do you / remember me? Umm! / I'm working part-time!",
    724: "I'm so happy~ Did you / come to check on / us? How nice of you!",
    725: "We'll do our best! / Well then, good luck / to you too, senpai!",
    726: "The Orc happily / returned to work.",
    727: "Part-timer's trust / went up by 5!",

    # Battle scene - woman in samurai armor vs warriors
    728: "A hair-raising / murderous energy swirled / as fierce shouts echoed.",
    729: "A woman in samurai / armor was surrounded / by strong warriors.",
    730: "It was a fierce battle, / but the woman was clearly / outmatched by their",
    731: "One of the warrior's / blows glanced off / the woman's shoulder.",
    732: "The warriors' blades / closed in on the / fallen woman.",
    733: "At this rate, the / woman in samurai armor / was going to die.",
    734: "Will you lend / your hand? / Help    Don't help",

    # You intervene
    735: "  plunged into / the crowd of warriors.",
    736: "Aoi! I'm sorry, / I owe you one.",
    737: "Aoi looked somewhat / wounded, her face / pale and deadly.",
    738: "The hooded man, who / had been watching from / a distance, approached.",
    739: "The man placed / himself in front / of Aoi.",

    # Mac Bain dialogue
    740: "Hooded Man: We are / both busy people. / Let's have a talk.",
    741: "Why are you / attacking me?",
    742: "As I said, I had no / intentions of harming / you. Wrong person?",
    743: "Aoi: Mac Bain, Mac Bain / Loudun. I will never / forget this name.",
    744: "Remember what you / did in the village / of Sura.",
    745: "You plundered the / village! You killed all / the innocent villagers.",
    746: "You forced young / children into the / church and killed them.",
    747: "The sound of their / cries still haunts / my ears!",
    748: "Aoi leapt backwards / and held her sword / at her side.",
    749: "Her eyes glowed pale / with murderous intent / and tremendous fury.",

    # Aoi's oath
    750: "\"I swore! I will find / you and avenge / them!\"",
    751: "\"Prepare yourself, / for this blade will / surely strike you!\"",

    # Mac Bain's response
    752: "Mac Bain: The village / of Sura? Huh, when / was that?",
    753: "I'm truly sorry, but / unfortunately I can / not remember.",
    754: "Don't be offended, / but for me, looting / and killing is like",
    755: "Do you remember / how many meals / you've eaten?",
    756: "You've never counted / them, and the same / goes for me.",
    757: "Mac Bain was smiling / wryly and kept / his cool.",
    758: "On the contrary, Aoi / could barely hold / her sword properly.",
    759: "Blood oozed from her / side, staining her / clothes red.",
    760: "Aoi finally / collapsed and fell / to her knees.",

    # Mac Bain backstory
    761: "Mac Bain: It is true / that we have done wrong / in many places.",
    762: "If you were among / them, then I am / truly sorry!",
    763: "But I am just too / busy to remember, / you know.",
    764: "Ever since I've been / stuck in this wretched / body, I have been",
    765: "Mac Bain took off his / armour and hood.",
    766: "What emerged was a / horrific sight / to behold.",
    767: "Behold this wretched / body!",
    768: "This body must be / fed with blood at / least once a day.",
    769: "Once, in my quest / for eternal life, / I tried secret arts,",
    770: "And as a result, / I have been burdened / with this cursed task!",
    771: "Since then, I have / been searching for / the Book of Darkness.",
    772: "I am running out / of time to keep / my body going.",
    773: "I know it.",
    774: "If I don't get the / Book of Darkness soon, / I will disappear into",
    775: "I am sorry, but you / are not allowed / to interfere.",
    776: "And for you, Name, / I am disappointed! / I thought you were",
    777: "You will pay for / turning the blade / on us.",

    # After Mac Bain fight
    778: "Mac Bain attacked / you and Aoi.",
    779: "You spotted a Bracelet / next to the collapsed / Mac Bain.",
    780: "You picked up the / Identification / Bracelet.",
    781: "From the thoughts / stored in the Bracelet, / you learned a new",
    782: "You obtained / Magic Shell!",
    783: "Aoi approached, / limping.",
    784: "Thank you! / It's over now!",
    785: "Aoi used her sword / as a walking aid / to support herself.",
    786: "She was so injured / and exhausted that / she could barely stand.",
    787: "Finally! The crying / children have found / their rest!",
    788: "Finally, finally! / I can tell / them now!",
    789: "She rejected your / attempt to lend / her a hand.",
    790: "Let me at least / walk by myself / one more time.",
    791: "\"If you ever need / my help, just come / and tell me.\"",
    792: "\"My life is / yours now.\"",
    793: "Aoi can now be / recruited at the / Adventurer's Guild.",

    # Alternative battle scene (re-enter without helping)
    794: "You decided to / leave it at that.",
    795: "The woman in samurai / armor was under / heavy attack.",
    796: "The woman tried to / fight off the blades, / but couldn't hold out.",
    797: "Will you lend / your hand? / Help    Don't help",
    798: "A hair-raising / murderous energy swirled / as fierce shouts echoed.",
    799: "A woman in samurai / armor was surrounded / by strong warriors.",
    800: "It was a fierce battle, / but the woman was clearly / outmatched by their",
    801: "One of the warrior's / blows glanced off / the woman's shoulder.",
    802: "The warriors' blades / closed in on the / fallen woman.",
    803: "At this rate, the / woman in samurai armor / was going to die.",
    804: "Will you lend / your hand? / Help    Don't help",
    805: "You decided to / leave it at that.",
    806: "The woman in samurai / armor was under / heavy attack.",
    807: "The woman tried to / fight off the blades, / but couldn't hold out.",
    808: "Will you lend / your hand? / Help    Don't help",

    # Sorcerer at waterway
    809: "Nearby, a sorcerer / was crouching by / the waterway.",
    810: "He was holding / a bottle and pouring / its contents into",
    811: "The sorcerer poured / the liquid in, then / quickly hid the bottle.",
    812: "The man came this way / to exit through / the passage.",
    813: "Sorcerer: Hello. / The water here is / delicious! Kukuku!",
    814: "Oh, hello. Running / errands for someone / again?",
    815: "That waterway? I / just put some really / effective medicine",
    816: "Well, drink it / at your own risk! / Hehehe!",
    817: "Oh! Could it be / you're running errands / for that person again?",
    818: "That water is safe. / I personally added / plenty of fine medicine",
    819: "How unfortunate! / Kukuku!",
    820: "Thirsty? If you want / to drink the water, / go ahead! Kukuku!",
    821: "The sorcerer left / with a wide grin / on his face.",

    # Aoi dialogue with companion
    822: "\"Please go back. / You don't need to / throw your life away.\"",
    823: "\"I can't just leave / Aoi here and / wait around!\"",

    # Samurai woman vs Order member scene
    824: "The woman in samurai / armor and an Order / member were fighting.",
    825: "Aoi: It's dangerous / but I'm going / alone.",
    826: "But, Captain!",
    827: "Aoi swiftly drew / her sword and struck / at the Order member.",
    828: "My one purpose / is to slay that man.",
    829: "I've finally / found him.",
    830: "I won't let anyone / interfere.",
    831: "Aoi's eyes were / pale and cold, / brimming with murderous",
    832: "Overwhelmed by the / killing intent from / her body, the Order",
    833: "Aoi spoke to the / retreating Order / member.",
    834: "Tell Ortrud / for me.",
    835: "I don't think this / is for my sake, but / thank you for bringing",
    836: "As Aoi was about / to leave, Vera / suddenly stopped her.",

    # Vera confrontation
    838: "\"Why are you / the only one / still alive!?\"",
    839: "Vera's voice / trembled with agitation / and anger.",
    840: "Aoi stopped walking / and slowly turned / around.",
    841: "Vera: Aoi, why are / you the only one / still alive?",
    842: "Vera's eyes blazed / with anger, ready / to attack her.",
    843: "Explain! What / happened to / the others!?",
    844: "Why are you the / only one left / alive!?",
    845: "Aoi kept her eyes / down and said / nothing.",
    846: "You won't answer? / Did you betray / Simson after all!?",
    847: "You should have / a look at this.",
    848: "Aoi offered / her a journal.",
    849: "You received / Simson's journal!",
    850: "Library: Simson's / journal has been / registered.",
    851: "I found this on / the eighth floor.",
    852: "If I had betrayed / him, it would be / written there.",
    853: "I was not allowed / to die. That's why / I separated from him.",
    854: "That's all / there is to it.",
    855: "I don't need honor / or gold.",
    856: "I have only one / wish: to cut off / the life of a certain",
    857: "Simson understood / that.",
    858: "If you still want / to slay me, / then do it.",
    859: "Aoi then turned / and walked away / unprotected.",

    # Vera's reaction
    861: "Vera tried to / follow her, but gave / up and stopped.",
    862: "I heard from Simson / that she is on / a vendetta.",
    863: "She's been wandering / the world looking / for one man.",
    864: "Simson trusted her / the most out of / all his companions.",
    865: "People call her / 'Manslayer,' but she / has a warm heart.",
    866: "I know in my heart / that it wasn't / her fault...",
    867: "But maybe Simson / didn't have to / die here...",
    868: "I still think / that, even now!",
    869: "Vera slumped her / shoulders and returned / to the ranks.",

    # Princess Oriana discovery reactions
    870: "Vera: Surprising! / The princess was / alive after all!",
    871: "What does this / statement mean?",
    872: "Surely Webster didn't / hide her in the / labyrinth out of spite?",
    873: "In that meeting / with the elder, they / said Webster held the",
    874: "Why would someone / hide the princess?",
    875: "The Duhan royal / family shouldn't have / the usual power",
    876: "If it was a joint / effort with the king, / the princess would be",
    877: "Indeed, none of / this makes any / sense at all.",
    878: "Konde: Surprising / that the princess / was alive.",
    879: "It's like a fairy / tale told to / children.",
    880: "A princess whose / life was stolen was / kept alive by magic.",
    881: "When he led his men / there, they found the / princess sleeping",
    882: "  thought the / princess had died / and returned to the castle.",
    883: "But the princess / was not dead.",
    884: "When the fairies / cast their magic / again, she was restored.",
    885: "We didn't realize / at the time, but / it was all a scheme.",
    886: "It's advanced alchemy. / By dissolving a / certain medicine in",
    887: "Well, if someone / did that, they must / have deep alchemy",
    888: "Just like the Elf / who was with the / lord earlier.",
    889: "Erika: Unbelievable! / I saw the princess / alive in there!",
    890: "It wasn't just me. / Many people bid / farewell to the princess",
    891: "I also made sure / no rats got near, / and kept watch.",
    892: "If she had been / alive then, I / would have noticed.",
    893: "With no water or / food, how could / anyone survive in there?",
    894: "Could it be that / her mind has / been damaged?",
    895: "That's the only / explanation / I can think of.",

    # Iris reaction
    896: "Iris! That was / unexpected.",
    897: "The princess being / alive is one thing, / but I thought Webster",
    898: "After all, that's / what everyone in / the kingdom believed.",
    899: "The Order is led / by Belgrano, and the / Royal Knights by",
    900: "But when you think / about it, it / makes sense.",
    901: "What that elder / said earlier / explains everything.",
    902: "After all, the Royal / Knights were formed / from the king's own",
    903: "When Ortrud acted, / and both the Order / and air corps were",
    904: "Only the Royal / Knights survived.",
    905: "In other words, / they are Ortrud's / most trusted allies.",
    906: "I don't know what / Webster is planning, / but this changes",
}

# Apply translations for 711-906
fixed_count = 0
for mi, eng in translations.items():
    if mi in r1208_idx:
        data[r1208_idx[mi]]["english"] = eng
        fixed_count += 1

# Count remaining problems
remaining = 0
for e in data:
    if e.get("resource") == 1208:
        if any(ord(c) > 127 for c in e.get("english", "")):
            remaining += 1
            print("REMAINING: msg_index=" + str(e["msg_index"]) + " EN=" + e["english"])

print("")
print("Translations applied for 711-906: " + str(fixed_count))
print("Remaining non-ASCII entries: " + str(remaining))

if remaining == 0:
    with open(INPUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("File saved successfully!")
else:
    print("NOT SAVING - still has remaining issues!")
