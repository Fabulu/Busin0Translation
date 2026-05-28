#!/usr/bin/env python3
"""build_glossary.py - Parse guide_full.txt and build structured glossary for Busin 0 translation."""

import json
import re
import os

GUIDE_PATH = r"C:\Programmieren\wizardrytranslation\dumps\guide_full.txt"
OUTPUT_PATH = r"C:\Programmieren\wizardrytranslation\data\glossary.json"

def read_guide():
    with open(GUIDE_PATH, "r", encoding="utf-8", errors="replace") as f:
        return f.readlines()

def build_spells():
    sorcery_spells = {
        1: [("KRETA", "fire"), ("TEAL", "electric"), ("SPLEEM", "sleep"), ("ANALYZE", "utility")],
        2: [("ZATEAL", "electric"), ("YAIBA", "undead"), ("THROUGH", "utility"), ("RIPU", "utility")],
        3: [("KURUDO", "cold"), ("ZAKRETA", "fire"), ("COAT", "buff"), ("FLOAT", "utility")],
        4: [("WEAK", "debuff"), ("JATEAL", "electric"), ("ZAKURUDO", "cold"), ("ESCAPE", "utility")],
        5: [("JAKRETA", "fire"), ("DELAY", "debuff"), ("SHROUD", "instant_death"), ("CANNIBAL", "drain")],
        6: [("ZASHROUD", "cold"), ("JAKURUDO", "instant_death"), ("DRAIN", "drain"), ("REFLECT", "buff")],
        7: [("MEGADEATH", "universal"), ("JASHROUD", "instant_death"), ("RAID", "universal"), ("VALHALLA", "utility")],
    }
    holy_spells = {
        1: [("HEAL", "healing"), ("BULLETS", "holy"), ("THIEFEYE", "utility"), ("PROTECT", "buff")],
        2: [("SAROME", "debuff"), ("FEEBLE", "debuff"), ("BLESS", "buff"), ("POIZEKEA", "cure")],
        3: [("STRAIN", "debuff"), ("DEEPS", "debuff"), ("PARAZKEA", "cure"), ("TRANS", "utility")],
        4: [("HEALS", "healing"), ("REPEAT", "utility"), ("AMOK", "holy"), ("FEARKEA", "cure")],
        5: [("RAHEAL", "healing"), ("POISON", "debuff"), ("RECOVER", "healing"), ("LUMIL", "utility")],
        6: [("WILL", "healing"), ("UNCURSE", "cure"), ("CARCASS", "resurrection"), ("VITAL", "buff")],
        7: [("STIGMA", "holy"), ("UNDEAD", "instant_death"), ("REVIVE", "resurrection"), ("OFFSET", "instant_death")],
    }
    sorcery_details = {
        "KRETA": {"target": "single", "description": "Fire damage to single enemy"},
        "TEAL": {"target": "single", "description": "Electric damage to single enemy"},
        "SPLEEM": {"target": "row", "description": "Sleep effect on enemy row"},
        "ANALYZE": {"target": "single", "description": "Analyze monster stats"},
        "ZATEAL": {"target": "row", "description": "Electric damage to enemy row"},
        "YAIBA": {"target": "single", "description": "Companion OFE buff, +undead hit"},
        "THROUGH": {"target": "single", "description": "Temporarily disables enemies"},
        "RIPU": {"target": "single", "description": "Return to city"},
        "KURUDO": {"target": "row", "description": "Cold damage to enemy row"},
        "ZAKRETA": {"target": "row", "description": "Fire damage to enemy row"},
        "COAT": {"target": "single", "description": "Companion +AGI buff"},
        "FLOAT": {"target": "single", "description": "Disables traps"},
        "WEAK": {"target": "single", "description": "Lower enemy OFE"},
        "JATEAL": {"target": "all", "description": "Electric damage to all enemies"},
        "ZAKURUDO": {"target": "row", "description": "Cold damage to enemy row"},
        "ESCAPE": {"target": "single", "description": "Escape from battle"},
        "JAKRETA": {"target": "all", "description": "Fire damage to all enemies"},
        "DELAY": {"target": "single", "description": "Lower enemy AGI"},
        "SHROUD": {"target": "single", "description": "Instant death chance"},
        "CANNIBAL": {"target": "single", "description": "Steals HP from companion"},
        "ZASHROUD": {"target": "all", "description": "Cold damage to all enemies"},
        "JAKURUDO": {"target": "row", "description": "Instant death chance on row"},
        "DRAIN": {"target": "single", "description": "Life drain from enemy"},
        "REFLECT": {"target": "single", "description": "Magic shield on companion"},
        "MEGADEATH": {"target": "all", "description": "Universal damage to all enemies"},
        "JASHROUD": {"target": "single", "description": "Instant death, ignores DEF"},
        "RAID": {"target": "single", "description": "Universal damage, ignores DEF"},
        "VALHALLA": {"target": "single", "description": "Grants wish, -1 LVL loss"},
    }
    holy_details = {
        "HEAL": {"target": "single", "description": "Heals companion HP"},
        "BULLETS": {"target": "single", "description": "Holy damage to single enemy"},
        "THIEFEYE": {"target": "single", "description": "Shows treasure count on floor"},
        "PROTECT": {"target": "single", "description": "Companion +DEF buff"},
        "SAROME": {"target": "row", "description": "Mute effect on enemy row"},
        "FEEBLE": {"target": "single", "description": "Lower enemy DEF"},
        "BLESS": {"target": "single", "description": "Companion +EVA buff"},
        "POIZEKEA": {"target": "single", "description": "Cure poison on companion"},
        "STRAIN": {"target": "row", "description": "Magical paralysis on enemy row"},
        "DEEPS": {"target": "row", "description": "Lower enemy EVA"},
        "PARAZKEA": {"target": "single", "description": "Cure paralysis on companion"},
        "TRANS": {"target": "single", "description": "Return to floor entrance"},
        "HEALS": {"target": "row", "description": "Heals companion row HP"},
        "REPEAT": {"target": "row", "description": "Multiple trap disarm attempts"},
        "AMOK": {"target": "single", "description": "Holy damage to single enemy"},
        "FEARKEA": {"target": "single", "description": "Cure fear on companion"},
        "RAHEAL": {"target": "all", "description": "Heals all companion HP"},
        "POISON": {"target": "row", "description": "Poison effect on enemy row"},
        "RECOVER": {"target": "single", "description": "Companion HP regeneration"},
        "LUMIL": {"target": "single", "description": "Cures dark fog"},
        "WILL": {"target": "single", "description": "Heals companion HP and condition"},
        "UNCURSE": {"target": "single", "description": "Removes curse from companion"},
        "CARCASS": {"target": "single", "description": "Resurrect companion, may fail"},
        "VITAL": {"target": "all", "description": "Party stamina buff"},
        "STIGMA": {"target": "all", "description": "Holy damage to all enemies"},
        "UNDEAD": {"target": "all", "description": "Instant death to all undead"},
        "REVIVE": {"target": "single", "description": "Resurrect companion, caster dies"},
        "OFFSET": {"target": "all", "description": "Instant death to all, caster dies"},
    }
    spells = {}
    for level, spell_list in sorcery_spells.items():
        for name, element in spell_list:
            entry = {"level": level, "school": "sorcery", "element": element}
            if name in sorcery_details:
                entry["target"] = sorcery_details[name]["target"]
                entry["description"] = sorcery_details[name]["description"]
            spells[name] = entry
    for level, spell_list in holy_spells.items():
        for name, element in spell_list:
            entry = {"level": level, "school": "holy", "element": element}
            if name in holy_details:
                entry["target"] = holy_details[name]["target"]
                entry["description"] = holy_details[name]["description"]
            spells[name] = entry
    return spells

def build_classes():
    return {
        "Fighter":     {"abbrev": "FIG", "tier": "basic", "alignment": ["good", "neutral", "evil"]},
        "Thief":       {"abbrev": "THI", "tier": "basic", "alignment": ["good", "neutral", "evil"]},
        "Mage":        {"abbrev": "MAG", "tier": "basic", "alignment": ["good", "neutral", "evil"]},
        "Priest":      {"abbrev": "PRI", "tier": "basic", "alignment": ["good", "neutral", "evil"]},
        "Bishop":      {"abbrev": "BIS", "tier": "advanced", "alignment": ["good", "neutral", "evil"]},
        "Alchemist":   {"abbrev": "ALC", "tier": "advanced", "alignment": ["good", "neutral", "evil"]},
        "Samurai":     {"abbrev": "SAM", "tier": "advanced", "alignment": ["good", "neutral", "evil"]},
        "Knight":      {"abbrev": "KNI", "tier": "advanced", "alignment": ["good"]},
        "Ninja":       {"abbrev": "NIN", "tier": "advanced", "alignment": ["evil"]},
        "Monk":        {"abbrev": "MON", "tier": "advanced", "alignment": ["good", "neutral"]},
        "Gizoku":      {"abbrev": "GIZ", "tier": "expert", "alignment": ["neutral", "evil"]},
        "Paladin":     {"abbrev": "PAL", "tier": "expert", "alignment": ["good"]},
        "Dark Knight": {"abbrev": "DAR", "tier": "expert", "alignment": ["evil"]},
        "Omnitsu":     {"abbrev": "OMN", "tier": "expert", "alignment": ["neutral", "evil"]},
        "Shogun":      {"abbrev": "SHO", "tier": "expert", "alignment": ["good", "neutral", "evil"]},
        "High Thief":  {"abbrev": "HIG", "tier": "expert", "alignment": ["good", "neutral", "evil"]},
    }

def build_attributes():
    return {
        "STR": "Strength",
        "INT": "Intelligence",
        "FTH": "Faith",
        "VIT": "Vitality",
        "AGI": "Agility",
        "LCK": "Luck",
    }

def extract_weapons(lines):
    return {
        "Dagger": [
            "Dagger", "Craftsman Dagger", "Assassins Dagger", "Dagger of Petrification",
            "Mystic Dagger", "Thief's Dagger", "Dagger of the Gale",
            "Cursed Orc Dagger", "Bloody Dagger", "Cursed Dagger", "Blade of the Slaughter"
        ],
        "Throwing Knives": [
            "Throwing Knives", "Windbreaker Throwing Knives", "Bird Killer Throwing Knives",
            "Throwing Knives of the Heavens"
        ],
        "Shortsword": [
            "Shortsword", "Magus Shortsword", "Shortsword of Amber",
            "Shortsword of the Spirit", "Ancient Shortsword", "Shortsword of the Ninja",
            "Arcane Shortsword", "Shortsword of Evil", "Shortsword of Homecoming",
            "White Bone Shortsword", "Banished Shortsword"
        ],
        "Longsword": [
            "Longsword", "Razor Longsword", "Magus Longsword",
            "Longsword of Swiftness", "Dragon Bone Longsword", "Longsword of Divine Speed",
            "Longsword of Betrayal", "Longsword of Darkness", "Longsword of the Dead",
            "Longsword of the Devil"
        ],
        "Greatsword": [
            "Greatsword", "Battlemage Greatsword", "Heavy Greatsword",
            "Greatsword of the Ogre", "Greatsword of the Flame",
            "Sword of Divine Speed", "Greatsword of the Majin"
        ],
        "Katana": [
            "Katana", "Craftsman Katana", "Dotanuki", "Kana Osafune",
            "Nagasone Kotetsu", "Kanesada", "Kikuichimonji", "Masamune", "Muramasa",
            "Katana of the Lost", "Katana of Sorrow", "Cursed Katana"
        ],
        "Handaxe": [
            "Handaxe", "Heavy Hatchet", "Silver Hatchet", "Craftsman Hatchet",
            "Razor Hatchet", "Thundergod Hatchet", "Flashing Hatchet",
            "Battlemage Greataxe"
        ],
        "Mace": [
            "Mace", "Mace of Faith", "Mace of Flames", "Mace of Prayer",
            "Holy Mace", "Mace of Shame", "Mace of Disbelief"
        ],
        "Flail": [
            "Flail", "Morningstar", "Flail of the Magus",
            "Flail of the Lion King", "Flail of Hatred"
        ],
        "Cudgel": [
            "Cudgel", "Hexagonal Cudgel", "Cudgel of Valor",
            "Cudgel of the Rakshasa", "Cudgel of the Six Arch Demons"
        ],
        "Wand": [
            "Wand of Sealing", "Wand of Perception", "Wand of Silence",
            "Wand of Healing", "Wand of Flames", "Wand of Small Frost",
            "Wand of Cloudkill"
        ],
        "Staff": [
            "Staff of Sealing", "Staff of Healing"
        ],
        "Knuckles": [
            "Knuckles", "Iron Knuckles", "Dragon Knuckles"
        ],
        "Shuriken": [
            "Shuriken", "Shuriken of the Spirit", "Shuriken of the Ninja",
            "Shuriken of Resentment"
        ],
        "Crossbow": [
            "Crossbow", "Crossbow of Desire", "Crossbow of Prayer"
        ],
        "Longbow": [
            "Longbow", "Longbow of Kindness"
        ],
    }

def extract_armor(lines):
    return {
        "Helmet": [
            "Helmet", "Steel Helmet", "Helmet of Patience", "Helmet of Metastasis",
            "Helmet of the Warrior", "Helmet of Evil", "Helmet of the Holy Knight",
            "Helmet of Tears", "Helmet of the Mad King", "Cursed Helmet", "Black Hood"
        ],
        "Robe": [
            "Robe", "Magus Robe", "Elf Robe", "Robe of Illusions",
            "Robe of the Saint", "Robe of Distraction", "Robe of Betrayal"
        ],
        "Leather Armor": [
            "Leather Armor", "Magus Leather Armor", "Leather Armor of the Hunter",
            "Leather Armor of the Spirit", "Leather Armor of Faith",
            "Leather Armor of Excellence", "Leather Armor of Betrayal",
            "Leather Armor of the Dead"
        ],
        "Chainmail": [
            "Chainmail", "Magus Chainmail", "Blessed Chainmail", "Dragonskin Chainmail",
            "Chainmail of the Dead"
        ],
        "Breastplate": [
            "Breastplate", "Demon's Breastplate", "Breastplate of Protection",
            "Breastplate of Reincarnation", "Breastplate of Heresy"
        ],
        "Full Plate": [
            "Full Plate"
        ],
        "Small Shield": [
            "Small Shield", "Small Shield of the Magus",
            "Small Shield of Neutrality", "Small Shield of Evil Spirits",
            "Small Shield of a Evil Deity"
        ],
        "Shield": [
            "Shield", "Shield of Excellence", "Shield of Evil", "Shield of the Mad King"
        ],
        "Gauntlets": [
            "Gauntlets", "Steel Gauntlets", "Gauntlets of Evil Thoughts",
            "Gauntlets of the Mad King"
        ],
        "Boots": [
            "Boots of Speed", "Magician's Boots"
        ],
        "Cloak": [
            "Cloak of the Bishop", "Cloak of Poison"
        ],
    }

def extract_accessories(lines):
    return {
        "Talisman": [
            "Decorative Talisman", "Statue Talisman", "Dusty Talisman",
            "Samurai Talisman", "Battlemage Talisman", "Holy Knight Talisman",
            "Saint Peter Talisman", "Cursed Talisman"
        ],
        "Hair Ornament": [
            "Lapis Hair Ornament", "Elf Hair Ornament", "Saint's Hair Ornament",
            "Silver Hair Ornament", "Water Hair Ornament", "Witch's Hair Ornament",
            "Cursed Hair Ornament"
        ],
        "Wristband": [
            "Orc Wristband", "Ogre Power Wristband", "Thief's Wristband",
            "Knight's Wristband", "Useless Orc Wristband", "Exhausting Wristband"
        ],
        "Ring": [
            "Magician's Ring", "Miri's Ring"
        ],
        "Other": [
            "Identification Bracelet"
        ],
    }

def extract_monsters(lines):
    monsters = []
    seen = set()
    pattern = re.compile(r'^([A-Z][A-Z\s\'\-]+?)\s+LVL(\d+)\s*$')
    class_pattern = re.compile(r'^(LVL\d+\s+[A-Z][A-Z\s]+?)\s+LVL(\d+)\s*$')
    for line in lines:
        stripped = line.strip()
        m = pattern.match(stripped)
        if not m:
            m = class_pattern.match(stripped)
        if m:
            name = m.group(1).strip()
            lvl = int(m.group(2))
            if any(skip in name for skip in (
                "CAST SORCERIES", "CAST HOLY", "POTENTIAL", "MUST BE",
                "ALLIANCE TRUST", "LEADER MUST")):
                continue
            key = (name, lvl)
            if key not in seen:
                seen.add(key)
                monsters.append({"name": name.title(), "level": lvl})
    monsters.sort(key=lambda x: x["level"])
    return monsters

def build_npcs():
    return [
        {"name": "Vera Almohad", "role": "companion", "class": "Knight", "race": "Human",
         "personality": ["Sociable", "Cautious"]},
        {"name": "Konde", "role": "companion", "class": "Mage", "race": "Human",
         "personality": ["Sociable", "Narcicist"]},
        {"name": "Erika", "role": "companion", "class": "Priest", "race": "Elf",
         "personality": ["Studious", "Moody"]},
        {"name": "Iris Jager", "role": "companion", "class": "Fighter", "race": "Human",
         "personality": ["Fraternal", "Anxious"]},
        {"name": "Frieder", "role": "companion", "class": "Automata", "race": "Automata",
         "personality": []},
        {"name": "Turgot Martell", "role": "companion", "class": "Ninja", "race": "Human",
         "personality": ["Cautious", "Anxious"]},
        {"name": "Lidi Wallenstein", "role": "companion/guide", "class": "Gizoku", "race": "Unknown",
         "personality": ["Sociable", "Adventurous"]},
        {"name": "Pipin", "role": "NPC", "class": "Unknown", "race": "Orc"},
        {"name": "Guillaume", "role": "NPC", "class": "Alchemist", "race": "Elf",
         "note": "Runs the Alchemy Guild"},
        {"name": "Mott", "role": "NPC", "class": "Unknown", "race": "Orc",
         "note": "Vigger Shop employee"},
        {"name": "Lute", "role": "NPC", "class": "Unknown", "race": "Human",
         "note": "Disguises as orc in labyrinth"},
        {"name": "Emilia", "role": "NPC", "class": "Unknown", "race": "Human",
         "note": "Disguises as orc in labyrinth"},
        {"name": "Melanie", "role": "NPC", "class": "Unknown", "race": "Pixie"},
        {"name": "Miri", "role": "NPC", "class": "Unknown", "race": "Pixie"},
        {"name": "Wesbell", "role": "lore", "note": "Former president of Jugurtha's Academy of Magic"},
        {"name": "Ortrud", "role": "lore", "note": "Holy King who defeated San-Goth forces"},
        {"name": "Simson", "role": "lore", "note": "Vera's former leader"},
    ]

def build_locations():
    return [
        {"name": "Duhan", "type": "city", "aka": "The Jewel of Venoa"},
        {"name": "Karman's Labyrinth", "type": "dungeon", "floors": "B1F-B11F + Post Game"},
        {"name": "Bar Luna Light", "type": "tavern"},
        {"name": "Adventurer's Guild", "type": "facility"},
        {"name": "Alchemy Guild", "type": "facility"},
        {"name": "Church of Salem", "type": "facility"},
        {"name": "Adventurer's Inn", "type": "facility"},
        {"name": "Vigger Shop", "type": "shop"},
        {"name": "Volola District", "type": "area"},
        {"name": "Self-Seraph Shop", "type": "shop"},
        {"name": "Venoa", "type": "country"},
        {"name": "San-Goth", "type": "kingdom", "note": "Enemy kingdom in lore"},
        {"name": "Illyria", "type": "kingdom", "aka": "Irikia", "note": "Konde's defunct homeland"},
        {"name": "Haris", "type": "city", "note": "Where Erika transferred from"},
        {"name": "Jugurtha", "type": "city", "note": "Academy of Magic location"},
        {"name": "Dialant", "type": "lost_city", "note": "Ancient elven city mentioned by Guillaume"},
    ]

def build_alleid_attacks():
    return {
        "attack": [
            {"name": "W-Slash", "chapter": 1, "req": "2 Front Row"},
            {"name": "Sonic Sword", "chapter": 1, "req": "2 Front Row (1 KNI/PAL/DAR)", "note": "W-Slash EX"},
            {"name": "Hold Attack", "chapter": 2, "req": "1 Front Row, 1 Back Row MP User"},
            {"name": "Weak Attack", "chapter": 2, "req": "1 Front Row, 1 Back Row Bishop", "note": "Hold Attack alt"},
            {"name": "Stun Smash", "chapter": 3, "req": "1 Front Row, 1 Back Row MP User"},
            {"name": "Fake Attack", "chapter": 3, "req": "1 Front Row, 1 Back Row (THI/GIZ/HIG)", "note": "Stun Smash alt"},
            {"name": "Slay Crash", "chapter": "Tavern #9", "req": "2 Front Row adjacent"},
            {"name": "Soul Crash", "chapter": "Tavern #9", "req": "2 Front Row (1 MON)", "note": "Slay Crash EX"},
            {"name": "Back Attack", "chapter": 4, "req": "2 Front Row"},
            {"name": "Zantsuki Iaijin", "chapter": 4, "req": "2 Front Row (1 SAM/BUS)", "note": "Back Attack alt"},
            {"name": "Concentrated Attack", "chapter": 6, "req": "3 Front Row"},
            {"name": "Gale Slash", "chapter": 6, "req": "3 Front Row (1 KNI/PAL/DAR)", "note": "Concentrated Attack alt"},
            {"name": "Sweep Attack", "chapter": 7, "req": "3 Front Row"},
            {"name": "SJ Attack", "chapter": 7, "req": "1 Front Row, 1 Back Row MP User"},
            {"name": "Nightmare Quake", "chapter": 7, "req": "1 Front, 1 Back Row", "note": "SJ Attack EX"},
            {"name": "Cross-Gauge Kill", "chapter": 8, "req": "2 Front, 2 Back Row MP Users"},
            {"name": "Multi-Jump Attack", "chapter": 9, "req": "3 Front Row"},
            {"name": "Warp Attack", "chapter": "Vigger Lottery", "req": "3 Front, 1 Back Row"},
            {"name": "Sacred Cross", "chapter": "Battle", "req": "1 Front, 1 Back Row (Dispel)"},
            {"name": "Rush", "chapter": "Battle", "req": "4 Party Members"},
        ],
        "defense": [
            {"name": "Front Guard", "chapter": 1, "req": "3 Front Row"},
            {"name": "Dense Formation", "chapter": "Battle", "req": "4+ Defend vs 7+ enemies"},
            {"name": "Evasive Maneuver", "chapter": 4},
            {"name": "Magic Shield", "chapter": 6, "req": "2 Back Row MP Users"},
            {"name": "Mirror Image", "chapter": 7, "req": "3 Back Row MP Users"},
            {"name": "Anti-Magic Shell", "chapter": 9, "req": "3 Back Row MP Users"},
        ],
        "support": [
            {"name": "Restrict Shot", "chapter": 1, "req": "2 Back Row"},
            {"name": "Magic Cancel", "chapter": 2, "req": "2 Back Row"},
            {"name": "Intercept", "chapter": 4, "req": "2 Front Row"},
            {"name": "Support Shot", "chapter": "Battle", "req": "Front Row + Back Row ranged"},
            {"name": "Back Cover", "chapter": 5, "req": "2 Front Row"},
            {"name": "Breath Cancel", "chapter": "50 Part Time Jobs", "req": "2 Back Row"},
        ],
        "magic": [
            {"name": "Concentrated Spell", "chapter": 2, "req": "3 Back Row MP Users"},
            {"name": "Magic Cooperation", "chapter": "Battle", "req": "2 Back Row MP Users"},
            {"name": "Enchant", "chapter": "Battle", "req": "1 Front, 1 Back Row MP User"},
            {"name": "Magic Rapid Fire", "chapter": "Battle", "req": "2 Back Row MP Users"},
            {"name": "Silence Breaker", "chapter": "Tavern #23", "req": "3 Back Row MP Users"},
        ],
    }

def build_personality_traits():
    return [
        {"name": "Adventurous", "likes": "Strong-Willed", "dislikes": "Pusillanimous"},
        {"name": "Tribal Love", "likes": "Same race", "dislikes": "Narcicist"},
        {"name": "Cooperative", "likes": "Cooperative", "dislikes": "Lonely"},
        {"name": "Intellectual", "likes": "Researchers", "dislikes": "Belligerent"},
        {"name": "Fraternal", "likes": "Cooperative", "dislikes": "Sadist"},
        {"name": "Sociable", "likes": "Large groups", "dislikes": "Lonely"},
        {"name": "Studious", "likes": "Intelligent", "dislikes": "Superstitious"},
        {"name": "Short-Tempered", "likes": "Bored", "dislikes": "Cautious"},
        {"name": "Anxious", "likes": "Fraternal", "dislikes": "Belligerent"},
        {"name": "Bold", "likes": "Bold", "dislikes": "Hoarder"},
        {"name": "Determined", "likes": "Adventurous", "dislikes": "Pusillanimous"},
        {"name": "Pusillanimous", "likes": "Pusillanimous", "dislikes": "Adventurous"},
        {"name": "Wasteful", "likes": "Wasteful", "dislikes": "Hoarder"},
        {"name": "Maiden Heart", "likes": "Maiden Heart", "dislikes": "Hot-Blooded"},
        {"name": "Lustful", "likes": "Narcicist", "dislikes": "Lustful"},
        {"name": "Sadist", "likes": "Lonely", "dislikes": "Fraternal"},
        {"name": "Belligerent", "likes": "Belligerent", "dislikes": "Anxious"},
        {"name": "Moody", "likes": "Moody", "dislikes": "Short-Tempered"},
        {"name": "Bored", "likes": "Short-Tempered", "dislikes": "Hoarder"},
        {"name": "Stupid", "likes": "Stupid", "dislikes": "Intelligent"},
        {"name": "Lonely", "likes": "Lonely", "dislikes": "Sociable"},
        {"name": "Just", "likes": "Just", "dislikes": "Sadist"},
        {"name": "Superstitious", "likes": "Superstitious", "dislikes": "Cautious"},
        {"name": "Cautious", "likes": "Cautious", "dislikes": "Bold"},
        {"name": "Hoarder", "likes": "Economist", "dislikes": "Wasteful"},
        {"name": "Collector", "likes": "Collector", "dislikes": "Wasteful"},
        {"name": "Hot-Blooded", "likes": "Hot-Blooded", "dislikes": "Maiden Heart"},
        {"name": "Ecologist", "likes": "Ecologist", "dislikes": "Wasteful"},
        {"name": "Economist", "likes": "Hoarder", "dislikes": "Stupid"},
        {"name": "Narcicist", "likes": "Intelligent", "dislikes": "Narcicist"},
    ]

def main():
    print("Reading guide...")
    lines = read_guide()
    print(f"  Read {len(lines)} lines")

    print("Building spells...")
    spells = build_spells()
    print(f"  {len(spells)} spells")

    print("Building classes...")
    classes = build_classes()
    print(f"  {len(classes)} classes")

    print("Building attributes...")
    attributes = build_attributes()

    print("Extracting weapons...")
    weapons = extract_weapons(lines)
    weapon_count = sum(len(v) for v in weapons.values())
    print(f"  {weapon_count} weapons in {len(weapons)} categories")

    print("Extracting armor...")
    armor = extract_armor(lines)
    armor_count = sum(len(v) for v in armor.values())
    print(f"  {armor_count} armor in {len(armor)} categories")

    print("Extracting accessories...")
    accessories = extract_accessories(lines)
    acc_count = sum(len(v) for v in accessories.values())
    print(f"  {acc_count} accessories in {len(accessories)} categories")

    print("Extracting monsters...")
    monsters = extract_monsters(lines)
    print(f"  {len(monsters)} unique monsters")

    print("Building NPCs...")
    npcs = build_npcs()
    print(f"  {len(npcs)} NPCs/companions")

    print("Building locations...")
    locations = build_locations()
    print(f"  {len(locations)} locations")

    print("Building alleid attacks...")
    alleid = build_alleid_attacks()
    alleid_count = sum(len(v) for v in alleid.values())
    print(f"  {alleid_count} alleid attacks in {len(alleid)} categories")

    print("Building personality traits...")
    traits = build_personality_traits()
    print(f"  {len(traits)} personality traits")

    glossary = {
        "spells": spells,
        "classes": classes,
        "races": ["Human", "Elf", "Gnome", "Dwarf", "Hobbit"],
        "attributes": attributes,
        "items": {
            "weapons": weapons,
            "armor": armor,
            "accessories": accessories,
        },
        "monsters": monsters,
        "npcs": npcs,
        "locations": locations,
        "alleid_attacks": alleid,
        "personality_traits": traits,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(glossary, f, indent=2, ensure_ascii=False)

    print(f"\nGlossary written to: {OUTPUT_PATH}")
    print(f"Total entries summary:")
    print(f"  Spells: {len(spells)} (28 sorcery + 28 holy)")
    print(f"  Classes: {len(classes)}")
    print(f"  Races: {len(glossary['races'])}")
    print(f"  Attributes: {len(attributes)}")
    print(f"  Weapons: {weapon_count}")
    print(f"  Armor: {armor_count}")
    print(f"  Accessories: {acc_count}")
    print(f"  Monsters: {len(monsters)}")
    print(f"  NPCs: {len(npcs)}")
    print(f"  Locations: {len(locations)}")
    print(f"  Alleid Attacks: {alleid_count}")
    print(f"  Personality Traits: {len(traits)}")

if __name__ == "__main__":
    main()
