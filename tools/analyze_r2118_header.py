"""Parse TEX0_1 register and other header info from R2118."""
import struct

data = open('C:/Programmieren/wizardrytranslation/build/textures_to_edit/R2118_tavern_background.raw', 'rb').read()

# TEX0_1 = 0x2000000665320000
tex0 = 0x2000000665320000
# TEX0_1 fields:
# TBP0 [13:0] - Texture buffer base pointer (in 256-byte units / 64-byte pages)
tbp0 = tex0 & 0x3FFF
# TBW [19:14] - Texture buffer width (in 64-pixel units)
tbw = (tex0 >> 14) & 0x3F
# PSM [25:20] - Pixel storage mode
psm = (tex0 >> 20) & 0x3F
# TW [29:26] - Texture width (2^TW)
tw = (tex0 >> 26) & 0xF
# TH [33:30] - Texture height (2^TH)
th = (tex0 >> 30) & 0xF
# TCC [34] - Texture color component (0=RGB, 1=RGBA)
tcc = (tex0 >> 34) & 1
# TFX [36:35] - Texture function
tfx = (tex0 >> 35) & 3
# CBP [50:37] - CLUT buffer base pointer
cbp = (tex0 >> 37) & 0x3FFF
# CPSM [55:51] - CLUT pixel storage mode
cpsm = (tex0 >> 51) & 0xF
# CSM [56] - CLUT storage mode
csm = (tex0 >> 55) & 1
# CSA [61:57] - CLUT entry offset
csa = (tex0 >> 56) & 0x1F
# CLD [63:62] - CLUT buffer load control
cld = (tex0 >> 61) & 7

psm_names = {0:'PSMCT32',1:'PSMCT24',2:'PSMCT16',10:'PSMCT16S',
             19:'PSMT8',20:'PSMT4',27:'PSMT8H',36:'PSMT4HL',44:'PSMT4HH'}

print(f'TEX0_1 = 0x{tex0:016X}')
print(f'  TBP0 = {tbp0} (base pointer, x256 bytes = offset {tbp0 * 256})')
print(f'  TBW  = {tbw} (buffer width in 64-pixel units = {tbw * 64} pixels)')
print(f'  PSM  = {psm} ({psm_names.get(psm, "UNKNOWN")})')
print(f'  TW   = {tw} (texture width = {1 << tw} pixels)')
print(f'  TH   = {th} (texture height = {1 << th} pixels)')
print(f'  TCC  = {tcc} ({"RGBA" if tcc else "RGB"})')
print(f'  TFX  = {tfx}')
print(f'  CBP  = {cbp} (CLUT base pointer, x256 bytes = offset {cbp * 256})')
print(f'  CPSM = {cpsm} ({psm_names.get(cpsm, "UNKNOWN")})')
print(f'  CSM  = {csm}')
print(f'  CSA  = {csa}')
print(f'  CLD  = {cld}')

print(f'\nDerived parameters:')
print(f'  Texture: {1<<tw}x{1<<th} pixels, format={psm_names.get(psm,"?")}')
print(f'  Buffer width: {tbw*64} pixels')
print(f'  CLUT format: {psm_names.get(cpsm,"?")}')

# Now analyze the rest of the header
print(f'\nHeader structure analysis:')
print(f'  0x00-0x0F: First 16 bytes (pre-GIF?)')
print(f'  0x10-0x1F: ?')
print(f'  0x20-0x2F: GIF PACKED tag (NLOOP=4, NREG=1, A+D)')
print(f'  0x30-0x6F: 4 A+D register writes (CLAMP, MIPTBP, TEX1, TEX0)')
print(f'  0x70-0x7F: ?')
print(f'  0x80-0xBF: ? (more header/control data)')
print(f'  0xC0-0xCF: zeros')
print(f'  0xD0+: pixel data starts (first byte = 0x{data[0xD0]:02X})')

# So the actual pixel data starts at 0xD0 = 208
# File: 264192 - 208 = 263984 bytes remaining
# 512*512 = 262144 pixels
# 263984 - 262144 = 1840 bytes for palette + any trailing data
# But palette is 1024 bytes, so 1840 - 1024 = 816 bytes extra?
# Unless there's more header between 0x70 and pixel data

# Check what's at 0x70-0xCF more carefully
print(f'\nDetailed look at 0x70-0xCF:')
for i in range(0x70, 0xD0, 4):
    val = struct.unpack_from('<I', data, i)[0]
    print(f'  {i:04x}: {val:#010x} ({val})')

# Actually, the MIPTBP1 and other registers suggest there might be
# additional GIF tags for the pixel data transfer (BITBLTBUF, TRXPOS, etc.)
# Let me check around 0x70-0xA0 for additional GIF tags
print(f'\nChecking for GIF tags in 0x70-0xD0:')
for off in range(0x70, 0xD0, 16):
    lo, hi = struct.unpack_from('<QQ', data, off)
    nloop = lo & 0x7FFF
    flg = (lo >> 58) & 3
    eop = (lo >> 15) & 1
    nreg = (lo >> 60) & 0xF
    print(f'  0x{off:04X}: lo=0x{lo:016X} hi=0x{hi:016X}')
    print(f'          NLOOP={nloop}, FLG={flg}, EOP={eop}, NREG={nreg}')
