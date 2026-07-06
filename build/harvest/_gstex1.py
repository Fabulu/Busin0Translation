import struct
gs=open("C:/programmieren/wizardrytranslation/build/harvest/_requestperfect/GS.bin","rb").read()
print("GS.bin size", len(gs))
# PCSX2 GS dump: privileged regs + GS register state. The 0x2000-byte GS priv regs region
# then 19*8 internal regs? Layout varies. Look for TEX1_1 (0x14) MMAG bit.
# PCSX2 freeze: the dump begins with a header. We'll just scan tail 8KB for the GS context regs.
# TEX1 layout: bit5 = MMAG (1=LINEAR/blur, 0=NEAREST). bit6-8 MMIN.
# Heuristic: in PCSX2 GSdump the per-context registers are stored; hard without parser.
# Report: examine whether any TEX1 in the freeze has MMAG=1.
# Many Busin draws use NEAREST. The "blur" is more likely the 16x16 PSMT4 tile upscaled
# by the sprite's UV vs XY (the glyph is drawn larger than its native ink) -> magnification.
print("Heuristic: per-glyph tiles are 16x16 native; if drawn into a >16px cell, magnification")
print("with LINEAR (MMAG=1) blurs. Lever = force MMAG=0 (NEAREST) in the 0x3060B0 sprite's TEX1,")
print("OR draw at integer 1:1 scale. Needs GS reg confirm of current MMAG.")
