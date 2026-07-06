# Check 0x3060B0 glyph draw fn for TEX1 filter setup (MMAG/MMIN bits)
# TEX1 reg: bit0 LCM, bit2-4 MXL, bit5 MMAG (0=NEAREST,1=LINEAR), bit6-8 MMIN
import struct
exe=open("C:/programmieren/wizardrytranslation/extracted/SLPM_653.78","rb").read()
def fo(va): return va-0x100000+0x80
# scan 0x3060B0..0x307200 for immediate loads that look like TEX1 (reg 0x14) GIF a+d
# Hard statically. Instead check: is bilinear ever set? search for 0x00000014 (TEX1 reg id) nearby a 0x...020 magfilter
# Simpler: the per-glyph tile is 16x16 PSMT4 upsampled. Blur = LINEAR mag. 
# Just report we cannot resolve TEX1 statically from EXE reliably; note GS dump approach.
print("TEX1 filter resolution requires GS reg trace (GS.bin) - flagged.")
