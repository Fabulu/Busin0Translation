#!/usr/bin/env python3
"""Fix translations that overflow the game's text boxes (>150 chars)."""
import json
import glob
import os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

fixes = {
    # batch_01
    (1196, 59): "Girl A: They won't / give us a sword!\nGirl B: The guide / says they're at / the Guild!\nGirl A: You need / a permit!\nGirl B: Then ask!",

    # batch_02
    (1200, 157): "\"If they're dead, / resurrection is / the only way.\" / \"But it costs a / fortune here!\" / \"Only the rich / can afford it.\"",
    (1200, 175): "\"Brave adventurers / risk their lives / so we may live / in peace.\" The / priest laid a cloth / over the face and / began to pray.",
    (1200, 183): "\"That's too much!\" / \"Too dependent on / the leader!\" / \"Sounds like a / fake wail!\" / Your excessive / display backfired.",
    (1200, 200): "Upon waking, you / saw your companion / holding your hand. / You shook them off. / Everyone was / shocked into a / long silence.",
    (1200, 201): "\"They died, got / resurrected, and / THAT's how they / act?!\" \"I'd beat / them!\" The crowd / rushed to explain.",
    (1201, 97): "Warrior: Ortrud's / soldiers are like / grandchildren! / Clerk: I see... / Warrior: Grandpa / came to visit, so / no complaints!",
    (1202, 76): "Fighter, Mage, / Thief, Priest, / Knight, Bishop, / Ninja, Samurai, / Alchemist, Monk, / Rogue, Crusader. / Mott suddenly / realized something.",

    # batch_03
    (1203, 1008): "Soldier A: She's / back! Unscathed! / Soldier B: How'd / it go? / Soldier A: Gave / Rudy's team a / Demon corpse! / Soldier B: Wow!",
    (1203, 1011): "Woman: Went to / floor 6, no sign / of Aurora. / Soldier C: No / leads? / Woman: Deep in / floor 2, I felt / a strange presence!",
    (1203, 1012): "Soldier D: Aurora? / Woman: No, more / ancient than that. / Soldier D: If you / say so, Aoi. / Soldier C: We'll / send scouts.",
    (1203, 1108): "Soldier: Where to? / Ingo: I'm outta / here! / Soldier: Captain / will be mad... / Ingo: Tell / Belgradno! I quit!",

    # batch_04
    (1204, 24): "Come, you too. / No more suffering. / Everything changes. / Come to me. / As more worms / gathered, the mass / grew and its tone / turned commanding.",
    (1204, 129): "Monster A: Please? / Monster B: Hmm... / Monster A: I need / it for Lepra Goods! / Monster B: Those / Cursed Armors are / nice! / Monster A: Mean!",
    (1204, 130): "Monster B: Fine, / I'll give you my / spare. / Monster A: Yay! / Monster B: Meet me / later, I don't / have it now. / Monster A: Sure!",
    (1204, 295): "Belgradno: Was / this the witch? / Soldier: Please / calm down, sir. / Belgradno: How / can I be calm? / They were killed / without a fight!",
    (1205, 98): "If you believe in / Gods, show them / your face. Your / powerless days end / now. The door to / darkness opens. / A requiem for / those who fall.",
    (1205, 330): "Orc F: \"What are / you gonna do?\" / Orc G: \"That / shield is really / important!\" / Orc A: \"You don't / know nothing!\"",
    (1205, 331): "Orc B: \"That beast / is hella strong!\" / Orc A: \"Try being / in our shoes!\" / Orc B: \"We had to / fight while / guarding the / princess!\"",
    (1205, 760): "Voice: \"Can't you / break this door?\" / Melanie: \"No way!\" / Voice: \"Get help!\" / Melanie: \"That's / even harder!\" / Voice: \"Hurry up!\"",

    # batch_06
    (1208, 77): "Explore thoroughly / Weapon list? / Warehouse 1-10 / Shadow Check",
    (1208, 106): "Girl A: \"That fool / is hopeless.\" / Girl B: \"You kept / calling him a fool, / so he ran off!\" / Girl A: \"I only / told the truth!\"",
    (1208, 107): "Girl B: \"Fools have / their uses! He had / endurance.\" / Girl A: \"True. He / carried our stuff / so we never had / to go back.\"",
    (1208, 108): "Girl A: \"Wandering / alone here is / insane! I refuse!\" / Girl B: \"Then what?\" / Girl A: \"Let's post / a request in town / for help.\"",
    (1209, 7): "Explore / Ability? / Misc1-10 / ShadowChk / Appraise / Gods? / Alleid1-8 / Request done.",
    (1209, 194): "A stack of papers / read: \"To mark the / Event Venue opening, / Vigger Friends now / accept new members!\"",
    (1209, 517): "My research shows / a doll needs about / 1,188,000 EXP to / gain its own heart. / Use that as a / reference.",
    (1209, 522): "My research shows / a doll needs about / 1,188,000 EXP to / gain its own heart. / Use that as a / reference.",
    (1209, 527): "My research shows / a doll needs about / 1,188,000 EXP to / gain its own heart. / Use that as a / reference.",
    (1209, 532): "My research shows / a doll needs about / 1,188,000 EXP to / gain its own heart. / Use that as a / reference.",
    (1209, 537): "My research shows / a doll needs about / 1,188,000 EXP to / gain its own heart. / Use that as a / reference.",
    (1209, 542): "My research shows / a doll needs about / 1,188,000 EXP to / gain its own heart. / Use that as a / reference.",

    # batch_07
    (1210, 1): "Explore / Ability? / Misc1-10 / ShadowChk / Appraise / Gods? / Alleid1-8 / Request done.",
    (1210, 101): "Accept him / his blood shall / be thy body / his flesh thy / sustenance / the followers / shall be one / with the great / one forevermore.",
    (1211, 1): "Explore / Ability? / Misc1-10 / ShadowChk / Appraise / Gods? / Alleid1-8 / Request done.",

    # batch_intro
    (1193, 0): "For thirty years, / Duhan was plunged / into blood and / terror. This war / would be known as / the Battle of / Banquo. The king / of San-Goth, / possessed by the / spirit of death, / led his army to / attack Duhan! /  /  / ",
    (1194, 0): "The Dark Lord / Ashira vanished / into the abyss. / The warriors were / sealed away as / the war of Duhan / drew to a close. / Ortrud too was / sealed with the / warriors of the / Battle of Banquo. / Fresh snow / blanketed the land / and peace came at / last. Princess / Oriana declared / herself queen. / \"Gone are the days / nations shed blood. / We must advance / against our common / enemy, for all / who live in Venoa, / and the brave who / have fallen. I / declare my oath / as guardian / against darkness. / Let me introduce / them to you.\" The / knights advanced / amid loud cheers. / \"The swords of our / beloved Venoa! / The noble Queen's / Guard, who fight / the darkness!\" / As confetti rained / down, this scene / became legend. / The tale of a fair / queen and her / Queen's Guard. / For now, we set / this tale aside.",

    # batch_r1198
    (1198, 9): "Adv. A: We have / injured of our own / to worry about! / Adv. B: I heard / they weren't even / hunting the witch / but had other / business.",
    (1198, 14): "Commander: This is / what happens when / you leave things to / Lord Webster! / Knight: Sir, you're / talking aloud!! / Commander: Let / them hear me!",
    (1198, 59): "His eyes glinted / like a blade, his / face etched with / sword wounds, and / his shaved head / rested on a neck / thick as a woman's / waist.",
}

if __name__ == '__main__':
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else 'fix'

    if mode == 'fix':
        total_fixed = 0
        for fn in sorted(glob.glob('data/type2_translated/batch_*.json')):
            d = json.load(open(fn, encoding='utf-8'))
            changed = False
            for e in d:
                key = (e['resource'], e['msg_index'])
                if key in fixes:
                    old = e['english']
                    new = fixes[key]
                    if old != new:
                        e['english'] = new
                        changed = True
                        total_fixed += 1
                        print(f'  Fixed R{key[0]}[{key[1]}]: {len(old)} -> {len(new)} chars')
            if changed:
                with open(fn, 'w', encoding='utf-8') as f:
                    json.dump(d, f, ensure_ascii=False, indent=2)
                print(f'  Wrote {fn}')
        print(f'\nTotal entries fixed: {total_fixed}')

    # Always verify
    print('\n--- Verification ---')
    problems = 0
    for fn in sorted(glob.glob('data/type2_translated/batch_*.json')):
        d = json.load(open(fn, encoding='utf-8'))
        for e in d:
            en = e.get('english', '')
            if en.startswith('['):
                continue
            if e['resource'] not in (1193, 1194):
                if len(en) > 150:
                    print(f'OVER: {fn} R{e["resource"]}[{e["msg_index"]}] ({len(en)})')
                    problems += 1
            else:
                for i, line in enumerate(en.split(' / ')):
                    if len(line) > 18:
                        print(f'LINE OVER: {fn} R{e["resource"]}[{e["msg_index"]}] line {i}: "{line}" ({len(line)})')
                        problems += 1
    if problems == 0:
        print('All entries within limits.')
    else:
        print(f'{problems} problem(s) remain.')
