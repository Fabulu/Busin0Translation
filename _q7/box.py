import struct
ee=open('_q7/chargen_ee.bin','rb').read()
# Need s3 live. s3 = ctx from jal 0x3028E0. Hard to get statically.
# Instead reason from disasm: draw-X = penX(0x1cc) + (lh 0x3e(s3) + s7); s7 = count*12.
# Original 0x1cc after centering = 0 - count*12. So draw-X = (-count*12 + sum_adv_i) + box(0x3e) + count*12
#                                                          = box(0x3e) + sum_adv_i.  count*12 CANCELS.
# => With Stage1 proportional advance and NO Stage3, text is LEFT-anchored at box+0x3e, proportional. CORRECT for left-align.
# Stage3 (0x1cc -= SUM/2) would add an UNCANCELLED -SUM/2 -> shifts left by SUM/2 = mild centering pull. 
print("Analysis: s7=count*12 (from v1 @0x307FF0) and 0x1cc=-count*12 (orig centering) CANCEL at draw.")
print("With Stage1 only: draw-X = box+0x3e + sum(ADV up to i). Left-anchored proportional. Matches screenshot intent.")
print("Stage3 sets 0x1cc=-SUM/2 (uncancelled) -> net -SUM/2 shift = half-centering. May be desired or not.")
