import json, re, sys

# Load source batch and existing translations
src = json.load(open('C:/Programmieren/wizardrytranslation/data/type2_translation_batches/batch_02_R1199_R1200_R1201_R1202.json','r',encoding='utf-8'))
existing = json.load(open('C:/Programmieren/wizardrytranslation/data/type2_translated/batch_02.json','r',encoding='utf-8'))

# Build lookup for existing translations
ex_map = {}
for e in existing:
    ex_map[(e['resource'], e['msg_index'])] = e['english']

# Translation dictionary for R1200, R1201, R1202
trans = {}

# ============================================================
# R1200 translations (245 entries) - Salem Church / Thurgo / Sister Erika / Fouquet quest
# ============================================================
trans[(1200, 0)] = "The Medal filled with / the power of valor / returned to the gods."
trans[(1200, 1)] = "From the depths of / Thurgo's temple came / a familiar figure."
trans[(1200, 2)] = "It was the person / you met on the 3rd / underground floor."
trans[(1200, 3)] = "It seems the wounds / have fully healed."
trans[(1200, 4)] = "Oh, it's you! Back / then was real rough, / thanks a lot."
trans[(1200, 5)] = "I'm in a pretty / bad situation now."
trans[(1200, 6)] = "So this is all / I can give you, but / please accept it."
trans[(1200, 7)] = "Received a / Scorpion Knife."
trans[(1200, 8)] = "We're being chased / by that crazy / beast-tamer!"
trans[(1200, 9)] = "That guy keeps / saying the most / ridiculous things."
trans[(1200, 10)] = "Being wounded and / dying are different / things, he says."
trans[(1200, 11)] = "Sure, if you beat / the witch the kingdom / will rejoice, but"
trans[(1200, 12)] = "why does a young / guy like me have / to do it, right?"
trans[(1200, 13)] = "He's the kind of / guy who just doesn't / get common sense."
trans[(1200, 14)] = "If I'm caught, / he'll just send me / to fight witches again."
trans[(1200, 15)] = "So I'll lay low / until things cool / down."
trans[(1200, 17)] = "Thurgo hurried off / as if fleeing."
trans[(1200, 18)] = "The quiet sound of / a pipe organ and / a chorus reading / scriptures fills the air."
trans[(1200, 19)] = "The people knelt, / praying to sense / an invisible force."
trans[(1200, 20)] = "Sister Erika, / please wait!"
trans[(1200, 21)] = "Suddenly, a / priest's loud cry / echoed through / the temple."
trans[(1200, 22)] = "A sister was / hurrying this way / at full speed."
trans[(1200, 23)] = "No matter how / many times you say / it, I won't change."
trans[(1200, 24)] = "A priest was / chasing after her."
trans[(1200, 25)] = "Right here, the / priest caught up / to her."
trans[(1200, 26)] = "Priest: Why do / you commit such / a reckless act?"
trans[(1200, 27)] = "You are trying to / abandon the people / crushed by sorrow."
trans[(1200, 28)] = "Do you think God / would approve of / such unlawful acts?"
trans[(1200, 29)] = "The priest's face / was pale with anger, / about to collapse."
trans[(1200, 30)] = "Sister: It pains / me that the priest / will not understand!"
trans[(1200, 31)] = "The sister prayed / before the altar / and turned her gaze."
trans[(1200, 32)] = "In the temple, / you could see the / faces of believers."
trans[(1200, 33)] = "The temple offers / various services, / but those in need / of healing are many."
trans[(1200, 34)] = "I, from Haris, / have only been in / this town a short time,"
trans[(1200, 35)] = "yet already many / adventurers have / lost their lives."
trans[(1200, 36)] = "Those who survived / are in terrible / condition."
trans[(1200, 37)] = "Priest, surely you / know of that man / Simzon."
trans[(1200, 38)] = "When he came to / this town, he was / full of confidence."
trans[(1200, 39)] = "The labyrinth took / all of that away."
trans[(1200, 40)] = "He has no bright / future left. His / eyes taken, he can / only cower in fear."
trans[(1200, 41)] = "I think his case / is truly tragic."
trans[(1200, 42)] = "But what good does / it do for you / to go to the maze?"
trans[(1200, 43)] = "Will you take a / sword and seek / revenge alone?"
trans[(1200, 44)] = "Your role is to / pray, not to fight."
trans[(1200, 45)] = "Those who need you / now are not the / troops but the people / in this temple."
trans[(1200, 46)] = "The sister bowed / her head, listening / to the priest's words."
trans[(1200, 47)] = "Her resolve was / firm, shown by the / trembling in her / slow-spoken words."
trans[(1200, 48)] = "The scriptures / say this:"
trans[(1200, 49)] = "The one weapon of / the holy temple / must shield the people / from all evil."
trans[(1200, 50)] = "The evil clearly / shows its form / within the labyrinth."
trans[(1200, 51)] = "Priest, I / understand what / you are saying."
trans[(1200, 52)] = "But I cannot / stand by knowing / evil's true nature!"
trans[(1200, 53)] = "That labyrinth is / shrouded in darkness / where God's voice / cannot reach."
trans[(1200, 54)] = "As a servant of / God, I cannot / simply look away."
trans[(1200, 55)] = "That is the reason / I have decided / to act. Please / understand."
trans[(1200, 56)] = "Sister Erika!"
trans[(1200, 57)] = "She's gone!"
trans[(1200, 58)] = "O people of God, / am I the one who / is mistaken?"
trans[(1200, 59)] = "The labyrinth's / darkness is endless. / Such deep darkness / can break any soul."
trans[(1200, 60)] = "Looking at those / who have died, / this is clear."
trans[(1200, 61)] = "I fear this. In the / depths of darkness, / half-hearted faith / is worthless."
trans[(1200, 62)] = "But now I can only / pray that her faith / will not be lost."
trans[(1200, 63)] = "The priest lowered / his head and walked / sadly back to / his chambers."
trans[(1200, 64)] = "Investigate. / Curiosity? / Topic 1 / Topic 2 / Topic 3 / Topic 4 / Topic 5 / Topic 6 / Topic 7 / Topic 8 / Topic 9 / Topic 10 / Shadow Check / Lab anger / God's grace? / Cursed Allayed 1 / Cursed Allayed 2 / Cursed Allayed 3 / Cursed Allayed 4 / Cursed Allayed 5 / Cursed Allayed 6 / Cursed Allayed 7 / Cursed Allayed 8 / Request completed."
trans[(1200, 65)] = "Priest Fouquet: / Oh my, I've been / expecting you."
trans[(1200, 66)] = "Upon entering / the temple, the / priest at his desk / came to greet you."
trans[(1200, 67)] = "I received word / from the tavern. / You wish to help / Salem Temple, yes?"
trans[(1200, 68)] = "No need to be / shy. We're short on / help ourselves."
trans[(1200, 69)] = "I am Priest / Fouquet. Pleased / to make your / acquaintance."
trans[(1200, 70)] = "Now then, let me / explain the task."
trans[(1200, 71)] = "Have you ever had / any treatment or / healing done at / a temple before?"
trans[(1200, 72)] = "Oh, no need to / answer that."
trans[(1200, 73)] = "I too am a / busy man, and sadly / I cannot do this / alone."
trans[(1200, 74)] = "That's not to say / I'm remembering / the faces of those / who came for help."
trans[(1200, 75)] = "In any case, / alchemy and magic / have advanced too / fast, and recovery / techniques suffer."
trans[(1200, 76)] = "Because of this, / Salem Temple, / which should be / revered, is treated / with contempt."
trans[(1200, 77)] = "Fouquet covered / his face and / cried out loudly."
trans[(1200, 78)] = "Oh, how deplorable!"
trans[(1200, 79)] = "Treatment and / healing should not / be done hastily / with herbs or magic!"
trans[(1200, 80)] = "Quick healing means / quick harm -- that is, / treating life / carelessly."
trans[(1200, 81)] = "Again, Fouquet / raised his voice."
trans[(1200, 82)] = "Oh, how terrifying!"
trans[(1200, 83)] = "So I have prepared / a scenario to / correct this grave / situation."
trans[(1200, 84)] = "Now, please listen."
trans[(1200, 85)] = "A bed holds a man. / He is the leader / of an adventuring / party. His companion / holds his cold hand / and weeps quietly."
trans[(1200, 86)] = "A pipe organ plays / a sad melody. The / choir sings a hymn / of requiem. The / priest places his / hand above the body / and begins chanting."
trans[(1200, 87)] = "A divine aura / emerges from the / priest's hand and / slowly descends / into the body. As / warmth returns, the / companion grips / the hand tighter."
trans[(1200, 88)] = "The adventurer / opens their eyes / to divine light. / Their companion's / face is blurred-- / not from poor sight, / but from great tears."
trans[(1200, 89)] = "Well, that's the / gist of it."
trans[(1200, 90)] = "Don't you think / this is far more / moving than simply / relying on herbs?"
trans[(1200, 91)] = "This is the ideal / way to perform / resurrection / at a temple."
trans[(1200, 92)] = "I want the public / to witness this / perfect ceremony / firsthand."
trans[(1200, 93)] = "So I need a dead / leader and a / grieving companion / to play the roles."
trans[(1200, 94)] = "However, the roles / must be authentic."
trans[(1200, 95)] = "An actually dead / leader -- mere / pretense lacks / conviction."
trans[(1200, 96)] = "I hate to ask, / but I need someone / to die and be / brought back to life."
trans[(1200, 98)] = "The grieving / companion's role / must also be real."
trans[(1200, 99)] = "So please act as / though you are truly / mourning your leader."
trans[(1200, 100)] = "Ideally, I'd like / acting skill / worthy of at least / a passing grade."
trans[(1200, 101)] = "The rest will be / done exactly per / the scenario."
trans[(1200, 102)] = "That about sums / it up."
trans[(1200, 103)] = "I'll give you / a copy of the / scenario. Please / memorize it before / the performance."
trans[(1200, 104)] = "'Sacred Ceremony / 1-4' has been / added to your files."
trans[(1200, 105)] = "0123456789- / Oh! I forgot the / most important / thing."
trans[(1200, 106)] = "Please bring enough / gold for the / resurrection fee."
trans[(1200, 107)] = "The less experience / one has, the harder / the resurrection. / It requires more / skilled hands."
trans[(1200, 108)] = "For instance, your / leader needs / [g] in gold."
trans[(1200, 109)] = "The amount may / change as they grow, / but keep this / as a reference."
trans[(1200, 110)] = "Well then, I'll be / waiting for you."
trans[(1200, 111)] = "I received word / from the tavern. / You wish to help / Salem Temple, yes?"
trans[(1200, 112)] = "I am Priest / Fouquet. Pleased / to make your / acquaintance."
trans[(1200, 113)] = "Hmm, but this is / troubling. Your / leader appears / to have died."
trans[(1200, 114)] = "The leader must / also be briefed on / the plan before / we proceed."
trans[(1200, 115)] = "I'm sorry, but / please resurrect / your leader first."
trans[(1200, 116)] = "We'll talk after / that."
trans[(1200, 117)] = "The priest turned / away expressionless / and returned to / his desk."
trans[(1200, 118)] = "Fouquet: Please / wait."
trans[(1200, 119)] = "As you were about / to leave, the priest / called out."
trans[(1200, 121)] = "Good, it seems you / died but have / safely recovered."
trans[(1200, 122)] = "Before explaining / the task from the / tavern, I need you / to hear this / several times."
trans[(1200, 123)] = "Time is short, so / let me explain / quickly."
trans[(1200, 124)] = "I am deeply / troubled."
trans[(1200, 125)] = "Due to rapid / advances in alchemy / and magic, recovery / techniques suffer."
trans[(1200, 126)] = "Because of this, / Salem Temple, / which should be / revered, is treated / with contempt."
trans[(1200, 128)] = "The priest noticed / you and called out."
trans[(1200, 129)] = "Good, it seems you / died but have / safely recovered."
trans[(1200, 130)] = "Before explaining / the task from the / tavern, I need you / to hear this / several times."
trans[(1200, 131)] = "When you came the / first time, someone / had died, so I had / to postpone."
trans[(1200, 132)] = "Time is short, so / let me begin."
trans[(1200, 133)] = "I am deeply / troubled."
trans[(1200, 134)] = "Due to rapid / advances in alchemy / and magic, recovery / techniques suffer."
trans[(1200, 135)] = "Because of this, / Salem Temple, / which should be / revered, is treated / with contempt."
trans[(1200, 136)] = "Fouquet: The / preparations for / Fouquet's temple / quest are ready."
trans[(1200, 137)] = "Fouquet: Call the / priest? / Yes    No"
trans[(1200, 138)] = "You gave the / priest a subtle / signal to not keep / him waiting."
trans[(1200, 139)] = "The priest, having / noticed the signal, / crept along the / temple wall to / meet you quietly."
trans[(1200, 140)] = "Ah, the actors are / here. You called me, / so the roles and / gold are prepared?"
trans[(1200, 141)] = "Are you ready? / Yes    No"
trans[(1200, 142)] = "I see, fully / prepared then. / How reassuring."
trans[(1200, 143)] = "Now I'll draw / the attention of / the public inside / the temple."
trans[(1200, 144)] = "From here, follow / the scenario. / No mistakes, / please."
trans[(1200, 145)] = "Oh, not ready yet? / Well, if the / preparations aren't / done, it can't / be helped."
trans[(1200, 146)] = "Please hurry. The / reputation of / Salem Temple is / at stake."
trans[(1200, 147)] = "Decided not to / do it for now."
trans[(1200, 148)] = "Oh, how pitiful!"
trans[(1200, 149)] = "The priest cried / out loudly, as if / the whole temple / could hear."
trans[(1200, 150)] = "Everyone in the / temple turned to / look."
trans[(1200, 151)] = "Even those outside / the temple rushed / in to see what / was happening."
trans[(1200, 152)] = "'What is it?' / 'Quiet please!' / 'What happened?' / 'I can't see!'"
trans[(1200, 153)] = "In an instant, / a crowd formed / around the priest."
trans[(1200, 154)] = "Fouquet: Everyone, / please listen."
trans[(1200, 155)] = "This adventurer / has lost a dear / leader and is / consumed by grief."
trans[(1200, 156)] = "In desperation, / they have come to / Salem Temple for / salvation!"
trans[(1200, 157)] = "'Well, if they're / dead, resurrection / is the only way.' / 'But it costs a / fortune here!' / 'Only the rich / can afford it.' / 'Carcass priests!' / 'I'd use herbs.'"
trans[(1200, 159)] = "Why did this / adventurer come / here instead of / using herbs or magic?"
trans[(1200, 160)] = "Because they don't / want to treat / their leader like / a mere object!"
trans[(1200, 161)] = "Herbs and magic / have side effects. / If resurrection / fails, the result / is permanent death!"
trans[(1200, 162)] = "Then not even / Salem Temple / could help."
trans[(1200, 163)] = "Truly, they want / to revive their / leader with pure / devotion."
trans[(1200, 164)] = "Come, suffering / adventurer. Offer / your gold to Salem / Temple for the / resurrection."
trans[(1200, 165)] = "0123456789- / As instructed, you / donated [g] to / the offering box."
trans[(1200, 166)] = "Many thanks. Now, / bring the leader / here."
trans[(1200, 168)] = "The priest waits / silently, pointing / to the bed to / lay the leader."
trans[(1200, 169)] = "The priest waits / silently, pointing / to the bed. / a: Lay on the bed / b: Seat on the bed / c: Lean against bed"
trans[(1200, 170)] = "You gently laid / the body on the / bed, but it slipped / and hit the bed / with a thud, / landing face up."
trans[(1200, 171)] = "'A corpse doesn't / move like a living / person!' The priest / positioned the / hands and adjusted / the body properly."
trans[(1200, 172)] = "You carefully / carried the body / and set it on the / bed. The audience / was moved seeing / the body firsthand."
trans[(1200, 173)] = "You placed the / body on the bed's / footrest. The / audience was not / pleased, muttering / about disrespect."
trans[(1200, 174)] = "'Now now, I know / the leader's death / upsets you, but / please compose / yourself.' The priest / helped you move / the body properly."
trans[(1200, 175)] = "'It is because / brave adventurers / risk their lives / that we may live / better.' The priest / placed a white / cloth over the face / and began to pray."
trans[(1200, 176)] = "It wasn't stated / explicitly, but you / understood it was / the signal for the / next performance."
trans[(1200, 177)] = "It wasn't stated / explicitly, but you / understood it was / the signal. / a: Lie beside them / b: Embrace and weep / c: Hold hand quietly"
trans[(1200, 178)] = "Following the / priest's signal, you / shifted the body / slightly and lay / beside it, face up / with eyes closed."
trans[(1200, 179)] = "To express deeper / grief, you lay next / to the leader / as if sharing / their fate. You / took their hand / and held it."
trans[(1200, 180)] = "Silence filled the / temple. Though the / priest and crowd / watched, no sound / could be heard. / You opened your / eyes after waiting."
trans[(1200, 181)] = "Everyone stared / with mixed feelings. / The priest was / still praying. You / quietly stepped / down and returned / to your place."
trans[(1200, 182)] = "To express deeper / grief, you clung / to the body and / wailed loudly, / shaking it. Your / cries echoed / through the temple."
trans[(1200, 183)] = "'I know it's sad, / but that's too much!' / 'Too dependent on / the leader!' / 'Sounds like a fake / wail to me!' / Your excessive / display backfired."
trans[(1200, 184)] = "Per the scenario, / you held the / leader's hand / and shed quiet / tears. The crowd / was moved to tears / as well."
trans[(1200, 185)] = "'Let us begin.' / The priest opened / his eyes and / removed the cloth. / He whispered to / the choir, who / began to play."
trans[(1200, 186)] = "Soon after the / priest's signal, the / pipe organ played / a sorrowful melody / as the crowd joined / in prayer."
trans[(1200, 187)] = "The priest placed / his hand above the / body and began / chanting the holy / words softly but / with precision."
trans[(1200, 188)] = "The priest placed / his hand above the / body and began / chanting. / a: Chant the prayer / b: Sing an original / c: Dance a prayer"
trans[(1200, 189)] = "The praying crowd / was reciting the / same prayer. You / joined them, / chanting the holy / words sincerely."
trans[(1200, 190)] = "Inspired by the / organ, you composed / an original song / for your leader, / singing with all / your heart."
trans[(1200, 191)] = "O Leader, / Leader please / we beg you / please come back / don't abandon us / please return"
trans[(1200, 192)] = "Listening to the / organ, your body / began to move / to the rhythm, / and you danced / freely."
trans[(1200, 193)] = "A dance of prayer / for resurrection. / The crowd watched / in stunned silence, / but their reaction / was warm."
trans[(1200, 194)] = "As the organ's / melody neared its / end, you gripped / the leader's hand / and prayed. The / priest's voice echoed / as consciousness / faded."
trans[(1200, 195)] = "Opening your eyes, / a divine golden / aura was emerging / from the priest's / hands."
trans[(1200, 196)] = "The light slowly / descended into / the body."
trans[(1200, 197)] = "As the light filled / the body, warmth / returned to the / once-cold skin."
trans[(1200, 198)] = "Through the priest's / ceremony, [name] / was safely revived."
trans[(1200, 199)] = "Through the priest's / ceremony, you were / safely resurrected. / a: Push companion away / b: Pretend to be dead / c: Hold companion's hand"
trans[(1200, 200)] = "Upon waking, you / noticed your / companion holding / your hand. You / roughly shook / them off. Everyone / was shocked. / After a long / silence, the crowd / spoke up."
trans[(1200, 201)] = "'What?! They died, / caused trouble, got / resurrected, and / THAT's how they / act?!' 'I'd beat / them up!' The crowd / and priest rushed / to explain."
trans[(1200, 202)] = "'It's not like / that! They just / woke up confused!' / The priest cried / out: 'You're alive / now! Nothing to / fear! Wake up!'"
trans[(1200, 203)] = "'It's not like / that! She just / woke up confused!' / The priest cried / out: 'You're alive / now! Nothing to / fear! Wake up!'"
trans[(1200, 204)] = "Though conscious, / you pretended to / still be dead. The / crowd began to / whisper among / themselves."
trans[(1200, 205)] = "'Did it fail?!' / 'But failed revivals / turn to ash!' / 'Temples are / different from / magic?' 'Can we / get a refund?!'"
trans[(1200, 206)] = "Fouquet hurriedly / covered. 'No, this / is normal! Like / when you haven't / walked in a long / time, the body / takes time to move!'"
trans[(1200, 207)] = "The priest checked / your pulse and / confirmed success, / then calmly said: / 'The pulse has / returned. [name], / please wake up!'"
trans[(1200, 208)] = "Upon waking, you / felt your companion / holding your hand. / You gently squeezed / back, and they / gripped tighter / in return."
trans[(1200, 209)] = "You slowly opened / your eyes. The / divine light was / blinding. You could / vaguely see people / around you."
trans[(1200, 210)] = "Gradually your / vision cleared. / Your companion's / face was still / blurry--not from / your eyes, but from / their tears."
trans[(1200, 211)] = "As you rose from / the bed, the crowd / erupted in / applause."
trans[(1200, 212)] = "'Lucky leader, / good companions!' / 'I want friends / like that!' / 'A little hugging / never hurts!' / 'Don't die again!'"
trans[(1200, 213)] = "By the time you / rose, most onlookers / were already / leaving."
trans[(1200, 214)] = "'Well, glad they / survived.' 'After / paying that much, / of course.' 'Herbs / look easier.' / 'Shouldn't have / died! Hahaha!'"
trans[(1200, 215)] = "The moment you / rose from the bed, / jeers erupted / from the crowd."
trans[(1200, 216)] = "'Coming all the / way here for this? / Not worth it!' / 'Temples are just / for show.' 'What a / terrible party!' / 'Go die again!'"
trans[(1200, 217)] = "The onlookers / left the temple / in disgust."
trans[(1200, 218)] = "After the crowd / had fully left, / the priest / approached again."
trans[(1200, 219)] = "Fouquet: His / expression was / gentle and his tone / soft as he thanked / you first."
trans[(1200, 220)] = "Wonderful acting! / Thanks to you, / Salem Temple's / image has improved!"
trans[(1200, 221)] = "Soon, the sick and / injured will come / rushing to the / temple, no doubt!"
trans[(1200, 222)] = "Now, please accept / this. Take it / without hesitation!"
trans[(1200, 223)] = "The priest handed / over a Holy Mantle / and a pouch of / gold."
trans[(1200, 224)] = "This gold is a / token of thanks / for your wonderful / performance."
trans[(1200, 225)] = "If you or your / companions are / injured or die, / please come again."
trans[(1200, 226)] = "I'm counting on / you! Farewell!"
trans[(1200, 227)] = "0123456789- / Received a / Priestess Mantle."
trans[(1200, 229)] = "His expression was / unchanged and cold, / not looking pleased / at all."
trans[(1200, 230)] = "Fouquet began / speaking bluntly."
trans[(1200, 231)] = "You committed / serious errors / in the performance."
trans[(1200, 232)] = "Since the acting / deviated from my / scenario, the / public's response / was poor."
trans[(1200, 233)] = "Well, one must / accept the outcome. / I'm also to blame / for not testing / you properly."
trans[(1200, 234)] = "So I'll give you / the reward mantle, / but reluctantly."
trans[(1200, 235)] = "The priest handed / over the reward / mantle grudgingly."
trans[(1200, 236)] = "If fewer people / come to Salem / Temple, it will be / your fault."
trans[(1200, 237)] = "You must reflect / on how poorly you / handled this task."
trans[(1200, 238)] = "And you should / devote more effort / to Salem Temple / to make amends!"
trans[(1200, 239)] = "Now, I am busy, / and your help is no / longer needed. / Farewell."
trans[(1200, 240)] = "0123456789- / Received a / Priestess Mantle."
trans[(1200, 241)] = "His expression / was one of rage, / and his body / trembled."
trans[(1200, 242)] = "How deplorable!"
trans[(1200, 243)] = "What exactly are / you people?! Shady / agents trying to / ruin Salem Temple?"
trans[(1200, 244)] = "You completely / ignored my scenario / and ruined it / with your careless / performance."
trans[(1200, 245)] = "Did you see those / people's faces, / as if mocking / our sacred work?"
trans[(1200, 246)] = "Salem Temple and / I have been scarred / for life because / of you!"
trans[(1200, 247)] = "Oh God! Is this / your trial for us?!"
trans[(1200, 248)] = "The priest clasped / his hands, muttering / toward the heavens."
trans[(1200, 249)] = "After staring / for a while, the / priest shouted."
trans[(1200, 250)] = "How long will you / stay?! Get out! / Never set foot / in this temple again!"
trans[(1200, 251)] = "You were thrown out / by the priest!"

# Load R1201 translations
exec(open('C:/Programmieren/wizardrytranslation/tools/tr02_part2.py','r',encoding='utf-8').read())
# Load R1202 translations
exec(open('C:/Programmieren/wizardrytranslation/tools/tr02_part3.py','r',encoding='utf-8').read())

# ============================================================
# Build the output
# ============================================================
output = []
for entry in src:
    r = entry['resource']
    idx = entry['msg_index']
    jp = entry['japanese']

    key = (r, idx)
    if key in ex_map:
        eng = ex_map[key]
    elif key in trans:
        eng = trans[key]
    else:
        eng = f"[UNTRANSLATED R{r} #{idx}]"
        print(f"WARNING: Missing translation for R{r} msg_index={idx}: {jp[:40]}...", file=sys.stderr)

    output.append({
        "resource": r,
        "msg_index": idx,
        "japanese": jp,
        "english": eng
    })

print(f"Total entries: {len(output)}")
assert len(output) == 936, f"Expected 936, got {len(output)}"

missing = [e for e in output if e['english'].startswith('[UNTRANSLATED')]
if missing:
    print(f"WARNING: {len(missing)} untranslated entries!")
    for m in missing[:20]:
        print(f"  R{m['resource']} #{m['msg_index']}: {m['japanese'][:50]}")
else:
    print("All 936 entries translated!")

outpath = 'C:/Programmieren/wizardrytranslation/data/type2_translated/batch_02.json'
with open(outpath, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print(f"Written to {outpath}")
