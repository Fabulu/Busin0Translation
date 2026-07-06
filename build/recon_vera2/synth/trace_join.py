import sys, struct, os
sys.stdout.reconfigure(encoding='utf-8')
# Array A Iris=[193,194,232,205] == pristine R1892 rec0 @0x142 VERBATIM (LE).
# Array A BABA=[34,33,34,33] raw glyph (player input).
# So array A copies R1892 name field VERBATIM as-is. The renderer then must convert:
#   for premade: stored 193-base -> R2100 kana cell ; for ASCII player input stored 33-base -> R2100 ascii cell.
# Test: is R1892 codec RAW-glyph (not +95)? rec0=[193,194,232,205]. If raw glyph into R2100,
#   glyph 193 = katakana cell. Earlier r2100_ascii_glyph_ids: A=33. katakana starts ~97.
#   The struct BABA=[34,33,...] raw glyph B=34,A=33 => RAW GLYPH, NOT +95.
# CONCLUSION: R1892 stores RAW R2100 glyph indices. The PATCHER WRONGLY used +95!
# Verify: patched Vera became [149,164,177,160]. As RAW glyph: 149,164,177,160 are KATAKANA cells, not ASCII!
#   So in array A/bar those would render as katakana garbage, NOT 'Vera'. THAT is why R1892 patch failed for the bar.
# Array B (recruit pool) showed 'Vera' only because we DECODED with -95; but if B is rendered with RAW-glyph
#   renderer, [149,164,177,160] = katakana cells too. Need to confirm renderer codec.
# Decisive test: BABA in array A = raw glyph [34,33,34,33]. The bar shows 'BABA'. R2100 ascii A=33 (raw). PROVEN raw.
# Therefore CORRECT romanized Vera in R1892 must be RAW glyph: V=54,e=69,r=82,a=65 -> [54,69,82,65].
print("CORRECT raw-glyph Vera name-values for R1892:", [54,69,82,65])
print("  bytes LE:", b''.join(struct.pack('<H',v) for v in [54,69,82,65]).hex())
print("WRONG (current patch, +95):", [149,164,177,160])
# Confirm english_glyph_table gives these:
import json
gt=json.load(open("C:/programmieren/wizardrytranslation/data/english_glyph_table.json",encoding='utf-8'))
print("V,e,r,a glyph ids:",gt['V'],gt['e'],gt['r'],gt['a'])
print("B,A glyph ids:",gt['B'],gt['A'],"(matches BABA raw [34,33])")
