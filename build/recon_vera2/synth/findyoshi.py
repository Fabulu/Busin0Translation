import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open("C:/programmieren/wizardrytranslation/build/recon_tri/extract/veraisjapanese__ee.bin","rb").read()
# yoshihoku よしほく. Hiragana. In array B, ascii uses glyph+95. Hiragana would be a different glyph block.
# Let's instead find the SECOND active member by looking at array A more carefully:
# The bar shows 2 members. array A has 6. Maybe bar only shows party that's "in formation".
# Reconsider: maybe screenshot's よしほく IS array A member but rendered via a name we misread.
# Let's render array A slot names as hiragana using base. Try: hiragana base such that よ maps.
# 50-on: あ=0..436 row. Hard. Instead: the bar 2nd name has 4 glyphs よ-し-ほ-く.
# Check: does array A have a 4-glyph member matching a hiragana run? slot1=193,194,232,205.
# If these were HIRAGANA (not katakana) base, 193=? We assumed katakana. Let me test hiragana hypothesis:
# Render full hiragana 50-on with base. Standard: BUSIN hiragana block likely base=146 or so.
# Brute: try bases b in 90..260, decode slot1 [193,194,232,205] as gojuon index (v-b) and see if forms readable.
gojuon="あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん"
for b in range(90,260):
    idx=[v-b for v in [193,194,232,205]]
    if all(0<=k<len(gojuon) for k in idx):
        s=''.join(gojuon[k] for k in idx)
        # check if looks like a name (no weird) - just print plausible
        print(f"base{b}: {s}")
