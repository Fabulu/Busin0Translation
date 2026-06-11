import struct, sys, os
sys.path.insert(0, 'C:/Programmieren/wizardrytranslation/tools')
from psmt8_deswizzle import deswizzle_psmt8
from psmt4_deswizzle import deswizzle_psmt4
from PIL import Image

path = 'C:/Programmieren/wizardrytranslation/extracted/packdata_raw/2138_type29.raw'
with open(path, 'rb') as f:
    data = f.read()

records = []
for i in range(29):
    rec_off = i * 16
    idx, size, offset, unk = struct.unpack_from('<IIII', data, rec_off)
    records.append((idx, size, offset, unk))

# --- Sub 5 ---
# type=0x11, 16 entries * 0x50 = 0x500 byte packet header, texture at +0x5A0
idx, size, offset, unk = records[5]
print("Sub5: size=%d, offset=0x%X" % (size, offset))
sub5 = data[offset:offset+min(0x600, size)]
print("Sub5 at 0x560-0x5C0:")
for j in range(0x560, 0x5C0, 16):
    print("  0x%04X: %s" % (j, ' '.join('%02X' % b for b in sub5[j:j+16])))

# Sub5: try PSMT8 256x256 at 0x5A0
abs_pix5 = offset + 0x5A0
pdata5 = bytes(data[abs_pix5:abs_pix5+65536])
linear5 = deswizzle_psmt8(pdata5, 256, 256, bw_psmt8=256, dbw_ct32=128)
img5 = Image.new('L', (256, 256))
for i, p in enumerate(linear5[:65536]):
    img5.putpixel((i % 256, i // 256), p)
fn5 = 'C:/Programmieren/wizardrytranslation/build/r2138_sub05_256x256.png'
img5.save(fn5)
print("Sub5 256x256 PSMT8: saved " + fn5)

# --- Sub 3 ---
# type=0x11, 9 entries * 0x50 = 0x2D0 byte header, texture at +0x2D0+0xA0 = 0x370
idx, size, offset, unk = records[3]
print("\nSub3: size=%d, offset=0x%X" % (size, offset))
# sub3: first dense block at? header = 9*0x50 = 0x2D0
# texture descriptor at 0x2D0, pixel data at 0x2D0+0xA0=0x370
abs_pix3 = offset + 0x370
# 10624 - 0x370 = 10624 - 880 = 9744 bytes available
# PSMT8 96x96 = 9216. PSMT8 100x96 = 9600. PSMT8 128x64 = 8192.
# PSMT4 128x128 = 8192.
# Try PSMT8 128x64 = 8192
pdata3 = bytes(data[abs_pix3:abs_pix3+8192])
linear3 = deswizzle_psmt8(pdata3, 128, 64, bw_psmt8=128, dbw_ct32=64)
img3 = Image.new('L', (128, 64))
for i, p in enumerate(linear3[:128*64]):
    img3.putpixel((i % 128, i // 128), p)
img3.save('C:/Programmieren/wizardrytranslation/build/r2138_sub03_128x64.png')
print("Sub3 128x64 PSMT8: saved")

# Also try PSMT4 128x128
pdata3b = bytes(data[abs_pix3:abs_pix3+8192])
linear3b = deswizzle_psmt4(pdata3b, 128, 128, bw_psmt4=128, dbw_ct32=64)
img3b = Image.new('L', (128, 128))
for i, p in enumerate(linear3b[:128*128]):
    brightness = (15-p)*17
    img3b.putpixel((i % 128, i // 128), brightness)
img3b.save('C:/Programmieren/wizardrytranslation/build/r2138_sub03_128x128_psmt4.png')
print("Sub3 128x128 PSMT4: saved")

# --- Sub 21 ---
# type=0x11, 11 entries * 0x50 = 0x370 header, texture at 0x370+0xA0 = 0x410
idx, size, offset, unk = records[21]
print("\nSub21: size=%d, offset=0x%X" % (size, offset))
abs_pix21 = offset + 0x410
# 18944 - 0x410 = 18944 - 1040 = 17904 bytes
# PSMT8 128x128 = 16384. 17904-16384=1520 (CLUT+pad OK)
pdata21 = bytes(data[abs_pix21:abs_pix21+16384])
linear21 = deswizzle_psmt8(pdata21, 128, 128, bw_psmt8=128, dbw_ct32=64)
img21 = Image.new('L', (128, 128))
for i, p in enumerate(linear21[:128*128]):
    img21.putpixel((i % 128, i // 128), p)
img21.save('C:/Programmieren/wizardrytranslation/build/r2138_sub21_128x128.png')
print("Sub21 128x128 PSMT8: saved")

# --- Sub 23 ---
# type=0x10, 8 entries * 0x50 = 0x280 header, texture at 0x280+0xA0 = 0x320
idx, size, offset, unk = records[23]
print("\nSub23: size=%d, offset=0x%X" % (size, offset))
abs_pix23 = offset + 0x320
# 35008 - 0x320 = 35008 - 800 = 34208 bytes
# PSMT8 256x128 = 32768. 34208-32768=1440 (CLUT+pad OK)
# Or PSMT4 256x256 = 32768
pdata23 = bytes(data[abs_pix23:abs_pix23+32768])
linear23 = deswizzle_psmt8(pdata23, 256, 128, bw_psmt8=256, dbw_ct32=128)
img23 = Image.new('L', (256, 128))
for i, p in enumerate(linear23[:256*128]):
    img23.putpixel((i % 256, i // 256), p)
img23.save('C:/Programmieren/wizardrytranslation/build/r2138_sub23_256x128.png')
print("Sub23 256x128 PSMT8: saved")

# Also try sub23 as PSMT4 256x256
linear23b = deswizzle_psmt4(pdata23, 256, 256, bw_psmt4=256, dbw_ct32=128)
img23b = Image.new('L', (256, 256))
for i, p in enumerate(linear23b[:256*256]):
    brightness = (15-p)*17
    img23b.putpixel((i % 256, i // 256), brightness)
img23b.save('C:/Programmieren/wizardrytranslation/build/r2138_sub23_256x256_psmt4.png')
print("Sub23 256x256 PSMT4: saved")

print("DONE")
