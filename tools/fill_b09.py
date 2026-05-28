import json, re, sys

with open("C:/Programmieren/wizardrytranslation/data/type2_translated/batch_09.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Build lookup by (resource, msg_index)
lookup = {}
for i, e in enumerate(data):
    key = (e["resource"], e["msg_index"])
    lookup[key] = i

# Translations dict: (resource, msg_index) -> english
translations = {}

# ========== R1353 placeholders (34 entries) ==========

translations[(1353, 67)] = "You have slain the / crawling ones and / now stand before me."
translations[(1353, 78)] = "Gather all your / strength."
translations[(1353, 88)] = "Even if you forget / the dead, as long as / you remember them, / they'll return."
translations[(1353, 92)] = "Received the / Floor Key."
translations[(1353, 96)] = "The floor is back!!"
translations[(1353, 97)] = "So this is what / it means!!"
translations[(1353, 122)] = "Lucy noticed you / and came over from / behind the counter."
translations[(1353, 131)] = "Lucy pulled a / secret potion from / her bag and drank / it in one gulp."
translations[(1353, 153)] = "Really, you sure?! / You don't have to / hold back!"
translations[(1353, 155)] = "Really, you sure?! / You don't have to / hold back!"
translations[(1353, 168)] = "Really, you sure?! / You don't have to / hold back!"
translations[(1353, 170)] = "Really, you sure?! / You don't have to / hold back!"
translations[(1353, 165)] = "What?! You don't / have 5000g?! / That's rough, bro~"
translations[(1353, 184)] = "A shout echoes / from somewhere."
translations[(1353, 187)] = "Poor thing, . / Leader with nothing!"
translations[(1353, 190)] = "Good for you, . / Nothing now, but / great things await!"
translations[(1353, 220)] = "Good you have gear. / Forgetting demons / is your thing, but / to them, you're the / real demon!"
translations[(1353, 258)] = "Has a powerful / familiar."
translations[(1353, 259)] = "With more training, / you could get an / incredible one."
translations[(1353, 260)] = "Sharp observation / skills. Good at / collecting too."
translations[(1353, 277)] = "Even with rare loot / from battle, it's / useless without / the right gear."
translations[(1353, 279)] = "Gear is lacking / now, but you'll / master it soon."
translations[(1353, 293)] = "Oh! It broke!"
translations[(1353, 357)] = "Only 1 bracelet, / so once won, prize / changes to next!"
translations[(1353, 394)] = "An ID Bracelet was / caught on the edge / of the pit."
translations[(1353, 440)] = "I read beauty's / records. I earn my / living reading the / fates of the sealed."
translations[(1353, 441)] = "You don't seem to / carry anything / of value!"
translations[(1353, 443)] = "Paid registration / fee of 1000g."
translations[(1353, 527)] = "What're you / saying?!"
translations[(1353, 532)] = "If you want the / witch dead, do it / yourself!"
translations[(1353, 533)] = "Ah, if only / I could."
translations[(1353, 550)] = "What if she dies?"
translations[(1353, 590)] = "For if one is an / elf, all know that / time transforms / the spirit."
translations[(1353, 604)] = "I came this deep, / but defeating / Aurora or saving / this land holds no / interest for me."

# ========== R1354 placeholders (300 entries) ==========

# m0-6: Opening scene - led to audience hall, greeted by Webster
translations[(1354, 0)] = "You were led to / the audience hall / and greeted by / Lord Webster."
translations[(1354, 1)] = "Webster: Zel just / sent a report."
translations[(1354, 2)] = "He found traces / of Her Highness. / You have my thanks."
translations[(1354, 3)] = "This confirms that / Her Highness' body / is hidden in the / labyrinth."
translations[(1354, 4)] = "I intend to send / a search party / immediately to / recover her body."
translations[(1354, 5)] = "At last, Her / Highness may find / peace."
translations[(1354, 6)] = "Now then, His / Majesty awaits. / Come this way."

# m7-8: Just as Webster was about to lead you, a shrill voice rang out
translations[(1354, 7)] = "Just as Webster / was about to lead / you to the king--"
translations[(1354, 8)] = "A shrill voice / echoed through / the hall."

# m9-11: Sepoi king quote (Wezbell's entrance)
translations[(1354, 9)] = "\"500 years ago, / the King of Sepoi / said this:\""
translations[(1354, 10)] = "\"He would send his / army east and take / a continent in / his lifetime.\""
translations[(1354, 11)] = "\"It would have been / possible, if not / for the hundred / thousand dead.\""

# m12: Old man in cloak approaching
translations[(1354, 12)] = "An old man in a / filthy cloak came / closer, shaking off / the knights."

# m14-16: Guards' reaction
translations[(1354, 14)] = "What are the / guards doing?!"
translations[(1354, 15)] = "No one noticed / him getting / this far?"
translations[(1354, 16)] = "Get him out / of here!"

# m17-18: Ortrud orders them to stop
translations[(1354, 17)] = "\"Let him through.\""
translations[(1354, 18)] = "\"It is the great / mage Wezbell. No / one here could / restrain him.\""

# m19: Ortrud ordered the knights to stop
translations[(1354, 19)] = "King Ortrud / ordered the / knights to stand / down."

# m20-23: Wezbell's history lesson
translations[(1354, 20)] = "The Rune Knights / of Gilten brought / 7 nations under / their rule in / just 2 years."
translations[(1354, 21)] = "The mages of the / Illyrian dynasty / had power to / move the stars."
translations[(1354, 22)] = "But they all / perished! Yes, / that woman / destroyed them!"
translations[(1354, 23)] = "Those once-great / nations have left / no trace in this / world."

# m24-28: Wezbell challenges Ortrud
translations[(1354, 24)] = "Do you know what / I speak of, / Ortrud?"
translations[(1354, 25)] = "Ortrud: How would / I know what the / great mage Wezbell / ponders?"
translations[(1354, 26)] = "I am not so / conceited."
translations[(1354, 27)] = "But you didn't / come here for a / history lesson."
translations[(1354, 28)] = "What do you wish / to tell me, great / mage Wezbell?"

# m29-34: Wezbell's accusations
translations[(1354, 29)] = "What are you / hiding, Ortrud?"
translations[(1354, 30)] = "Why is Duhan / still alive?"
translations[(1354, 31)] = "Why has that / woman done / nothing for six / months?"
translations[(1354, 32)] = "If she were / serious, she could / not only curse / you--"
translations[(1354, 33)] = "but destroy all / of Duhan with / ease."
translations[(1354, 34)] = "You know / something. Tell me."

# m35-39: Ortrud's defense
translations[(1354, 35)] = "Don't intimidate / me, Wezbell. We / have enough / problems already."
translations[(1354, 36)] = "My daughter was / killed, and this / decaying curse / cripples me."
translations[(1354, 37)] = "That labyrinth / forced us to halt / trade between / nations."
translations[(1354, 38)] = "You've seen how / Duhan has fallen / into despair."
translations[(1354, 39)] = "You'd have me / invite even more / misfortune?"

# m40-44: Wezbell presses further
translations[(1354, 40)] = "I just want / to know."
translations[(1354, 41)] = "Why the man once / feared as the / Lion King, who led / war-torn Venoa / to peace--"
translations[(1354, 42)] = "now only sends / huddled masses as / a strike force?"
translations[(1354, 43)] = "Why let the witch / do as she / pleases?"
translations[(1354, 44)] = "Why hold back the / holy knights and / leave the holy / beasts unsealed?"

# m45-49: Ortrud's rebuttal
translations[(1354, 45)] = "Wezbell, no more / riddles. What are / you implying?"
translations[(1354, 46)] = "That I have some / secret pact with / Aurora?"
translations[(1354, 47)] = "That the witch / obediently kills / my daughter, / curses my body, / and creates the / labyrinth?"
translations[(1354, 48)] = "Hmph, ridiculous!"
translations[(1354, 49)] = "Instead of such / conspiracy / theories, join the / strike force!"

# m50-53: Wezbell decides to go
translations[(1354, 50)] = "Hmm! So you're / saying I'm free / to investigate?"
translations[(1354, 51)] = "What's to fear? / Whoever slays the / witch becomes / Duhan's new hero."
translations[(1354, 52)] = "And I eagerly / await that. That / is my only wish."
translations[(1354, 53)] = "Very well. I'll / gather companions / and head into the / labyrinth myself."

# m54-59: Webster/Zel aftermath
translations[(1354, 54)] = "Webster, who had / watched the / exchange, approached / with a puzzled / look."
translations[(1354, 55)] = "Who was that?"
translations[(1354, 56)] = "The shell of one / once known as the / great mage."
translations[(1354, 57)] = "Aurora took / everything from / him. Now he is / but a shadow."
translations[(1354, 58)] = "Forgive the / unexpected / interruption."
translations[(1354, 59)] = "Now, won't you / show me the ring / you found?"

# m60-66: Examining the ring
translations[(1354, 60)] = "King Ortrud took / the ring from you / and confirmed it / was the princess'."
translations[(1354, 61)] = "This is indeed / Oriana's. But why / was it in the / labyrinth?"
translations[(1354, 62)] = "What interest / does he have in / her body? Why / spread her scent?"
translations[(1354, 63)] = "I don't know. But / this proves / someone hid Her / Highness' body / in the labyrinth."
translations[(1354, 64)] = "I too shall enter / the labyrinth and / join the strike / force."
translations[(1354, 65)] = "Rest assured. / I will fulfill / Her Highness' / last wishes."
translations[(1354, 66)] = "With a warm / smile, Webster / departed."

# m67-78: Ortrud's reflections after
translations[(1354, 67)] = "Ortrud, who had / watched it all, / spoke quietly."
translations[(1354, 68)] = "Adventurer, how / curious. Many / have gathered here / in Duhan."
translations[(1354, 69)] = "Good and evil / alike fight to / make their dreams / come true."
translations[(1354, 70)] = "Some venture in / to reclaim what / they once lost."
translations[(1354, 71)] = "Others head to / the labyrinth to / realize unseen / ambitions."
translations[(1354, 72)] = "Whatever they / hold in their / hearts, it could / save Duhan."
translations[(1354, 73)] = "It matters not / who. If anyone / in this world can / defeat Aurora--"
translations[(1354, 74)] = "I would give up / this throne."
translations[(1354, 75)] = "Ortrud stared at / you intently."
translations[(1354, 76)] = "Perhaps you are / the one."
translations[(1354, 78)] = "With a gentle / smile, Ortrud / departed."

# m79-86: First meeting with Webster
translations[(1354, 79)] = "You entered the / castle and were / led to a hall."
translations[(1354, 80)] = "Knight: So you're / the new member of / the strike force."
translations[(1354, 81)] = "Captain Belgradno / sent a report."
translations[(1354, 82)] = "Said a promising / recruit arrived."
translations[(1354, 83)] = "I am Lord / Webster, Ferry / Leffort. Grand / chancellor of / this kingdom."
translations[(1354, 84)] = "I expect we'll be / working together. / Pleased to meet / you."
translations[(1354, 85)] = "Webster gave a / small smile."
translations[(1354, 86)] = "Webster: Come, / this way. King / Ortrud awaits. / Tell him about / the strike force."

# m87-98: First audience with Ortrud
translations[(1354, 87)] = "You were led to / the throne."
translations[(1354, 88)] = "King Ortrud sat / supported by / attendants, frail / and unsteady."
translations[(1354, 89)] = "The king skipped / formalities and / got straight to / the point."
translations[(1354, 90)] = "Ortrud: Recently, / attacks on the / convoys have / grown worse."
translations[(1354, 91)] = "There are rumors / that adventurers / have turned / hostile."
translations[(1354, 92)] = "We must face the / enemy united. / Such incidents / cannot be / ignored."
translations[(1354, 93)] = "I ask again: was / the convoy attack / the work of / monsters?"
translations[(1354, 94)] = "Who attacked the / convoy? / Monsters / Not sure"
translations[(1354, 95)] = "So it was / monsters, just as / previous reports / stated."
translations[(1354, 96)] = "Good grief, we've / barely scratched / the surface."
translations[(1354, 97)] = "The knights with / the convoy were / all found dead in / the labyrinth."
translations[(1354, 98)] = "How terrible, to / die unable to / clear their names / on the field."

# m100-106: Alternate answer path
translations[(1354, 100)] = "All convoy / incidents were / planned by the / Order itself."
translations[(1354, 101)] = "You recalled the / poisoned wounds / on the convoy / woman."
translations[(1354, 103)] = "An Order member / wouldn't need / poison; they have / many other ways."
translations[(1354, 104)] = "There is only / one answer."
translations[(1354, 105)] = "Before the / monsters attacked, / the convoy had / contact with / someone."
translations[(1354, 106)] = "Good to know."

# m108-118: Continued audience
translations[(1354, 108)] = "All convoy / incidents were / planned by the / Order itself."
translations[(1354, 109)] = "Ridiculous!"
translations[(1354, 110)] = "The king glared / and sighed / heavily."
translations[(1354, 111)] = "How pathetic."
translations[(1354, 112)] = "This body decays / from the witch's / curse. I can / barely walk."
translations[(1354, 113)] = "If only I were / free of this / curse, I'd go / investigate / myself!"
translations[(1354, 114)] = "I thank you, . / For your hard / work."
translations[(1354, 115)] = "An attendant held / out a shining / crossbow."
translations[(1354, 116)] = "Got Magic Crossbow."
translations[(1354, 117)] = "It's enchanted. / Useful against / the undead."
translations[(1354, 118)] = "Accept it as / thanks for your / hard work."

# m119-133: Ortrud asks your purpose
translations[(1354, 119)] = "Adventurer, may / I ask you / something?"
translations[(1354, 120)] = "Why do you / explore the / labyrinth?"
translations[(1354, 121)] = "For gold? For / glory? Or do you / fight without / purpose?"
translations[(1354, 122)] = "Your purpose? / For gold / For glory / No purpose"
translations[(1354, 124)] = "Once I had / nothing. Born to / a minor lord, I / could barely / afford a sword."
translations[(1354, 125)] = "But looking back, / I had everything."
translations[(1354, 126)] = "Friends to trust, / dreams worth / risking your life / for--everything."
translations[(1354, 127)] = "I became king / of Duhan. Got the / gold and glory."
translations[(1354, 128)] = "But everything / I once had is / now gone."
translations[(1354, 129)] = "Take this advice / from one who was / once like you."
translations[(1354, 130)] = "Find a friend you / can truly trust."
translations[(1354, 131)] = "A friend to watch / your back in / battle--no amount / of gold can buy / that."
translations[(1354, 132)] = "They won't just / save your life. / They'll help you / achieve / everything."
translations[(1354, 133)] = "Gold, glory, / dreams-- / everything."

# m134-148: Glory answer / No purpose answer
translations[(1354, 134)] = "Hmm, for glory."
translations[(1354, 135)] = "Once I had / nothing. Born to / a minor lord, I / could barely / afford a sword."
translations[(1354, 136)] = "But looking back, / I had everything."
translations[(1354, 137)] = "Friends to trust, / dreams worth / risking your life / for--everything."
translations[(1354, 138)] = "I became king / of Duhan. Got the / gold and glory."
translations[(1354, 139)] = "But everything / I once had is / now gone."
translations[(1354, 140)] = "Take this advice / from one who was / once like you."
translations[(1354, 141)] = "Find a friend you / can truly trust."
translations[(1354, 142)] = "A friend to watch / your back in / battle--no amount / of gold can buy / that."
translations[(1354, 143)] = "They won't just / save your life. / They'll help you / achieve / everything."
translations[(1354, 144)] = "Gold, glory, / dreams-- / everything."
translations[(1354, 145)] = "Then let me say / this. Find a / friend you can / truly trust."
translations[(1354, 146)] = "A friend to watch / your back in / battle--no amount / of gold can buy / that."
translations[(1354, 147)] = "They won't just / save your life. / They'll help you / achieve / everything."
translations[(1354, 148)] = "Gold, glory, / dreams-- / everything!"
translations[(1354, 149)] = "Heh, this illness / makes me too / sentimental."
translations[(1354, 150)] = "That's enough for / today. Time for / my doctor's / foul medicine."
translations[(1354, 151)] = "Supported by / attendants, King / Ortrud departed."

# m152-165: First meeting with Belgradno
translations[(1354, 152)] = "Inside the castle, / you were led to / a room resembling / a study."
translations[(1354, 153)] = "Well-furnished, / but practical-- / no decorations, / plain tapestries / and tablecloths."
translations[(1354, 154)] = "Belgradno: Sorry / to keep you. / Please, sit."
translations[(1354, 155)] = "Belgradno laid a / velvet pouch and / documents on / the table."
translations[(1354, 156)] = "The velvet was / expensive, but / the documents / bore the royal / seal--contracts / and reports."
translations[(1354, 157)] = "Right now, Duhan / faces a crisis."
translations[(1354, 158)] = "The recruitment / of adventurers-- / it's all because / of this crisis."
translations[(1354, 159)] = "The crisis is / the emergence / of monsters."
translations[(1354, 160)] = "You know of / Karman's Labyrinth / at the city / outskirts?"
translations[(1354, 161)] = "Their numbers are / small, but / monsters are / emerging from it."
translations[(1354, 162)] = "What we ask is / that you enter / the labyrinth and / bring back the / witch's head."
translations[(1354, 163)] = "The witch's name / is Aurora."
translations[(1354, 164)] = "An ancient evil, / personification / of destruction."
translations[(1354, 165)] = "That witch cursed / all of Duhan and / created the / labyrinth."

# m166-181: Aurora appears at the engagement ceremony flashback
translations[(1354, 166)] = "It was six months / ago, at Princess / Oriana and Lord / Webster's / engagement."
translations[(1354, 167)] = "\"It's been a / while, Your / Majesty.\""
translations[(1354, 168)] = "A woman with / dark, shining eyes / approached King / Ortrud."
translations[(1354, 169)] = "\"Au-Aurora!!\" / \"You look well.\" / \"What did you / come here for?\""
translations[(1354, 170)] = "Unrest spread / among the crowd."
translations[(1354, 171)] = "Everyone knew / that fearsome / name. The witch / who brought many / kingdoms to ruin."
translations[(1354, 172)] = "\"What brings you?\" / \"Everyone awaits.\" / \"Your Majesty, / remember your / promise?\""
translations[(1354, 173)] = "\"Speak! What do / you want?\" / \"This kingdom, / Duhan itself.\""
translations[(1354, 174)] = "A groan filled / the hall. All / watched with / dread and awe."
translations[(1354, 175)] = "\"You want Duhan?\" / \"Yes.\" / \"Insane?\" / \"I speak my heart.\""
translations[(1354, 176)] = "Soldiers rushed / toward the witch."
translations[(1354, 177)] = "But her gaze / froze them all. / No one could / move an inch."
translations[(1354, 178)] = "\"Is that your / answer?\" / \"Think as you / wish.\""
translations[(1354, 179)] = "\"Then walk the / path of ruin. / Your body shall / wither, you shall / be a wreck.\""
translations[(1354, 180)] = "The witch left / with her curse."
translations[(1354, 181)] = "Soon after, / disasters plagued / the royal line. / The witch had / cursed the king."

# m182-196: Belgradno's request
translations[(1354, 182)] = "Belgradno: We / must defeat her / and lift the / curse on Duhan."
translations[(1354, 183)] = "If you bring / Aurora's head, / the reward is / yours to choose."
translations[(1354, 184)] = "Even information / helps. Anything / useful will be / rewarded."
translations[(1354, 185)] = "Will you join the / strike force and / lend us your / strength?"
translations[(1354, 186)] = "Join the strike / force? Yes / No"
translations[(1354, 187)] = "I see. Caution / is a fine virtue / for an adventurer."
translations[(1354, 188)] = "No pressure, but / if you ever want / to help Duhan, / come see me."
translations[(1354, 189)] = "I'll be waiting / here."
translations[(1354, 190)] = "Quick decisions / are the mark of / a good leader."

# m191-201: Re-enter and accept
translations[(1354, 191)] = "Belgradno: So? / Ready to join / the strike force?"
translations[(1354, 192)] = "Or did you come / just to sightsee / and go home?"
translations[(1354, 193)] = "Join the strike / force? Yes / No"
translations[(1354, 194)] = "At last, you've / decided."
translations[(1354, 195)] = "I believe this / will bring you / rare experience / and adventure."
translations[(1354, 196)] = "Still undecided? / Very well, take / your time."
translations[(1354, 197)] = "Belgradno showed / you the royal / contract and the / reward's scale."
translations[(1354, 198)] = "Vast lands, a / castle, your own / army--a kingdom / of your own."
translations[(1354, 199)] = "These terms were / written by the / king himself."
translations[(1354, 200)] = "As long as Duhan / stands, this / contract will be / honored."
translations[(1354, 201)] = "Belgradno handed / you the velvet / pouch."

# m204-212: ID Bracelet and instructions
translations[(1354, 204)] = "This bracelet / identifies you / as strike force."
translations[(1354, 205)] = "All who enter / the labyrinth / must wear one."
translations[(1354, 206)] = "Don't store it. / Keep it on your / wrist at all / times."
translations[(1354, 207)] = "Our knights and / many adventurers / are in the / labyrinth."
translations[(1354, 208)] = "Without it, / you could be / attacked--and no / one's to blame."
translations[(1354, 209)] = "You put on the / ID Bracelet."
translations[(1354, 210)] = "I visit the / labyrinth often / to encourage the / adventurers."
translations[(1354, 211)] = "Come find me when / you're ready."
translations[(1354, 212)] = "If you need / supplies, visit / the Salem church / first."

# m213-231: Zel scene in labyrinth
translations[(1354, 213)] = "\"I hear the / convoy was / attacked.\""
translations[(1354, 214)] = "A figure emerged / from the shadows-- / Zel, head of the / ninja unit."
translations[(1354, 215)] = "Zel: I received / word that you / encountered / bandits on the / 3rd floor."
translations[(1354, 216)] = "We rushed there, / but you'd already / dealt with them."
translations[(1354, 218)] = "Don't misunder- / stand. Those / bandits fled here / long ago."
translations[(1354, 219)] = "Nothing to do / with us. Just / scum."
translations[(1354, 220)] = "We planned to / handle them / eventually."
translations[(1354, 221)] = "Thank you for / dealing with / them for us."
translations[(1354, 222)] = "Zel gave a brief / nod, but his / cold expression / revealed nothing."
translations[(1354, 223)] = "I have one more / matter."
translations[(1354, 224)] = "Show me the ring / you obtained."
translations[(1354, 225)] = "The ring from / a man named Ingo."
translations[(1354, 227)] = "Hmm. This seal / is indeed Her / Highness'. No / doubt about it."
translations[(1354, 228)] = "Well found. This / is a clue to / locating Her / Highness' body."
translations[(1354, 229)] = "Go to the castle."
translations[(1354, 230)] = "His Majesty will / be pleased."
translations[(1354, 231)] = "Zel's figure / melted into the / shadows."

# m232-262: Town scene - Simson the madman
translations[(1354, 232)] = "Heavy fog hung / low, and the / town was shrouded / in silence."
translations[(1354, 233)] = "Not a soul in / sight. Even the / wind had stopped. / The town was / deathly still."
translations[(1354, 234)] = "This was not the / proud jewel of / Venoa you'd / heard about."
translations[(1354, 235)] = "A bleak, dreary / town with no / trace of its / former glory."
translations[(1354, 236)] = "As you surveyed / the town, a / man's voice came / from the fog."
translations[(1354, 237)] = "\"Hey, tell me / where the priest / is hiding!\""
translations[(1354, 238)] = "A man stumbled / toward you."
translations[(1354, 239)] = "Hair unkempt, / clothes filthy, / eyes unfocused, / face twisted / in terror."
translations[(1354, 240)] = "Stranger: Hehehe, / you know where / the priest is, / right?"
translations[(1354, 241)] = "C'mon, tell me! / I gotta report / what I saw!"
translations[(1354, 242)] = "Heh, I know / you're hiding the / priest's location!"
translations[(1354, 243)] = "Better hurry. / It's for your / own good."
translations[(1354, 244)] = "The man forced / a grin and / glared at you."
translations[(1354, 245)] = "Aha, I see. You / don't know about / what happened."

translations[(1354, 246)] = "That's why you're / hiding the priest? / Hah, figures."
translations[(1354, 247)] = "But I saw it!"
translations[(1354, 248)] = "Yeah, they were / there. Hiding / in the dark."
translations[(1354, 249)] = "Let your guard / down, and they / come crawling / at you."
translations[(1354, 250)] = "Heh, my friends / got chomped from / behind."
translations[(1354, 251)] = "Munch, chomp. / Munch, chomp."
translations[(1354, 252)] = "The man made / exaggerated / biting motions, / as if mocking."
translations[(1354, 253)] = "No matter what / we did--useless!"
translations[(1354, 254)] = "Some cried and / begged for their / lives."
translations[(1354, 255)] = "Hahahaha! / Ahahahahaha!"
translations[(1354, 256)] = "His hysterical / laughter echoed / through the town."
translations[(1354, 257)] = "The man knelt, / clutching his / stomach, laughing."
translations[(1354, 258)] = "Tears in his / eyes, drool on / his chin--he / didn't notice."
translations[(1354, 259)] = "Ahahaha! Some / fought with all / they had!"
translations[(1354, 260)] = "But no matter / what--useless, / useless!"
translations[(1354, 261)] = "Can't blame 'em. / Even God would / die to that."

# m263-276: Sister and Simson
translations[(1354, 263)] = "\"What are you / doing out here?\""
translations[(1354, 264)] = "A nun came / running toward / you."
translations[(1354, 265)] = "Sister: I looked / everywhere! / You'll catch cold / dressed like that!"
translations[(1354, 266)] = "Your meal is / ready. Please / come eat."
translations[(1354, 267)] = "The man called / Simson followed / the nun to the / church."
translations[(1354, 268)] = "Please don't / judge him. He / fought for this / town."
translations[(1354, 269)] = "I heard he was / once a famous / mercenary / captain."
translations[(1354, 270)] = "But Karman's / Labyrinth broke / his mind."
translations[(1354, 271)] = "Since then he's / wandered the / town, afraid of / something."
translations[(1354, 272)] = "I don't know / what he saw."
translations[(1354, 273)] = "But it must have / been terrible / enough to drive / a strong man / mad."
translations[(1354, 274)] = "You look like an / adventurer too."
translations[(1354, 275)] = "A difficult path. / You risk your / life for what / you seek."
translations[(1354, 276)] = "I pray that peace / be with you."

# m278-311: Second visit - town scene with elf twins
translations[(1354, 278)] = "Heavy fog hung / low, and the / town was shrouded / in silence."
translations[(1354, 279)] = "Not a soul in / sight. Even the / wind had stopped. / The town was / deathly still."
translations[(1354, 280)] = "This was not the / proud jewel of / Venoa you'd / heard about."
translations[(1354, 281)] = "A bleak, dreary / town with no / trace of its / former glory."
translations[(1354, 282)] = "As you surveyed / the town, girls' / whispers came / from the fog."
translations[(1354, 283)] = "\"A new one's / here!\" / \"Tough?\" / \"A stray?\" / \"Let's go see!\""
translations[(1354, 284)] = "From the fog / emerged a pair of / elf girls."
translations[(1354, 285)] = "Elf girl: Hey, / you're the new / adventurer, / right?"
translations[(1354, 286)] = "We saw you / checking in at / the entrance."
translations[(1354, 287)] = "Young-faced twins, / one blonde, one / brunette--nearly / identical."
translations[(1354, 288)] = "You're going into / Karman's Labyrinth / too, aren't you?"
translations[(1354, 289)] = "No one can leave / this town because / of the labyrinth."
translations[(1354, 290)] = "Sigh... it's so / depressing."
translations[(1354, 291)] = "Ever since the / princess died, / nothing but / bad news."
translations[(1354, 292)] = "Monsters, the / town blockaded, / and the king / gravely ill."
translations[(1354, 293)] = "They say the / witch in the / labyrinth is / behind it all, / but no one's / found her yet."
translations[(1354, 294)] = "Which means / everyone here / is useless."
translations[(1354, 295)] = "What about you?"
translations[(1354, 296)] = "Think you can / find her?"
translations[(1354, 297)] = "If you defeat / the witch, an / amazing reward / awaits!"
translations[(1354, 298)] = "We did a / divination. The / stars told us."
translations[(1354, 299)] = "Soon, something / will change / Duhan's fate."
translations[(1354, 300)] = "That's why we're / watching for new / adventurers."
translations[(1354, 301)] = "And there's one / more thing."
translations[(1354, 302)] = "More people are / having ominous / dreams."
translations[(1354, 303)] = "A terrifying / nightmare! The / town in darkness, / everyone dies!"
translations[(1354, 304)] = "We don't know / what it means, / but something / big is coming."
translations[(1354, 305)] = "We're concerned / about it."
translations[(1354, 306)] = "The twins / lowered their / voices."
translations[(1354, 307)] = "\"Emilia, let's / go!\" \"Right, / they noticed!\" / \"If caught again, / no going out!\""
translations[(1354, 308)] = "We have things / to do. See you / around!"
translations[(1354, 309)] = "I'm Emilia."
translations[(1354, 310)] = "I'm Lute. We / both live in the / castle. See ya!"
translations[(1354, 311)] = "The elf girls / hurried back / into the fog."


# ========== Apply translations ==========
filled = 0
for key, english in translations.items():
    if key in lookup:
        idx = lookup[key]
        old = data[idx].get("english", "")
        if not old or old.startswith("[?]") or old == data[idx].get("japanese", ""):
            data[idx]["english"] = english
            filled += 1
        else:
            # Already translated, skip
            pass
    else:
        print(f"WARNING: key {key} not found in data", file=sys.stderr)

# Verify remaining placeholders
remaining = [e for e in data if not e.get("english") or e["english"].startswith("[?]") or e["english"] == e.get("japanese", "")]
print(f"Filled {filled} entries. Remaining placeholders: {len(remaining)}")
if remaining:
    for e in remaining[:30]:
        print(f"  R{e['resource']} m{e['msg_index']}: {e['japanese'][:60]}")

with open("C:/Programmieren/wizardrytranslation/data/type2_translated/batch_09.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Done. File saved.")
