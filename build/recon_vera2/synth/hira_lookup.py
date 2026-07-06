import sys, struct, json
sys.stdout.reconfigure(encoding='utf-8')
# Build hiragana char->glyph from hiragana_glyph_map grid. The grid stores 6 stride-57 ids per row.
# Standard 50-on layout: rows are あ-row consonants. Need char->id. Use katakana_glyph_map style mapping
# Simpler: the EXE name-entry stored values for player names are the SAME name-value codec as struct.
# The struct uses values where katakana base=193 (ラ). For hiragana, find the run for よしほく directly by brute search
# over plausible small u16 values that form a 4-char terminated-by-FFFF run near a 0x80xx header is not in struct.
# Instead: search EE for ANY 4-value run, FFFF-terminated, of values 95..400, that appears EXACTLY once and is NOT in roster.
ee=open("C:/programmieren/wizardrytranslation/build/recon_tri/extract/veraisjapanese__ee.bin","rb").read()
# We will instead look at what the renderer reads. Find the leader pointer.
# Known: BABA at 0x55DD22. The bar's leader label says "Leader". Let's find pointers to 0x55DD20.
target=0x55DD20
pb=struct.pack('<I',target)
i=0;hits=[]
while True:
    j=ee.find(pb,i)
    if j<0: break
    hits.append(j); i=j+1
    if len(hits)>40: break
print("pointers to 0x55DD20:",[hex(h) for h in hits])
# also pointer to slot1 (Iris) 0x55DF10
for name,addr in [("slot1",0x55DF10),("slot0name",0x55DD22)]:
    pb=struct.pack('<I',addr); i=0;h=[]
    while True:
        j=ee.find(pb,i)
        if j<0:break
        h.append(j);i=j+1
        if len(h)>20:break
    print(name,hex(addr),"->",[hex(x) for x in h])
