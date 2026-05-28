import zipfile, struct
z = zipfile.ZipFile(C:/Programmieren/wizardrytranslation/fight1.p2s, r)
data = z.read(eeMemory.bin)
target1 = bytes([110, 136, 99, 130])
hits1 = []
pos = 0
while True:
    pos = data.find(target1, pos)
    if pos == -1:
        break
    ctx_start = max(0, pos - 8)
    ctx_end = min(len(data), pos + 4 + 8)
    ctx = list(data[ctx_start:ctx_end])
    pre = pos - ctx_start
    hits1.append((pos, ctx, pre))
    pos += 1
print(Single-byte su-ra-i-mu hits:, len(hits1))
for offset, ctx, pre in hits1[:40]:
    print( offset=, hex(offset), ctx=, ctx, target@, pre)
    if pre >= 2 and ctx[pre-2] == 137:
        print( Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso ENGLISH GUIDE.pdf Firstdialogue.p2s Firsttavernrequestlistchoice.p2s NameEntryEuropean.p2s NameEntryHiraganamode.p2s NameEntryRandomCrap.p2s Nameentrystate.p2s Wizardry - Tale of the Forsaken Land (USA).bin Wizardry - Tale of the Forsaken Land (USA).cue Wizardry - Tale of the Forsaken Land (USA).iso build data debug_atlas.py debug_atlas.txt debug_atlas2.py debug_atlas2.txt debug_atlas3.py debug_atlas3.txt debug_header.py debug_header.txt debug_nibble.py debug_nibble.txt debug_swizzle.py debug_swizzle.txt dis1.py dis2.py dis3.py dis4.py docs download_model.py download_model.txt dumps ee_memory_fight1.bin extract_glyphs_8x8.txt extracted extracted_busin1 fight1.p2s fight2.p2s find_hira2.py find_hira4_code.txt find_hiragana_table.py firsttavern.p2s firsttavernbulletinboard.p2s firsttavernnarration.p2s greentext.p2s greentextgnome.p2s knighterguy.p2s knightguy.ps2.p2s lotsoftextgnome.p2s normaldungeonscreen.p2s ocr_glyphs.py ocr_glyphs.txt popup-tent popup-tent.zip randomdialogue.p2s release runs scan_exe.py scan_exe2.py scan_exe3.py scan_glyphs.py scan_glyphs2.py scan_glyphs3.py search_party_names.py skills test123.txt test_ocr.py test_ocr.txt test_ocr2.py test_ocr2.txt test_ocr3.py test_ocr3.txt test_ocr4.py test_ocr4.txt tools xref_search.py HAS ri=137!)
name_sjis = bx83x6fx83x75x83x8ax81x5bx83x58x83x89x83x43x83x80
pos3 = data.find(name_sjis)
print(Shift-JIS hit:, hex(pos3) if pos3 >= 0 else None)
name_utf8 = bxe3x83x90xe3x83x96xe3x83xaaxe3x83xbcxe3x82xb9xe3x83xa9xe3x82xa4xe3x83xa0
pos4 = data.find(name_utf8)
print(UTF-8 hit:, hex(pos4) if pos4 >= 0 else None)
