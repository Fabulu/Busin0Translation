
import struct, sys
sys.path.insert(0, 'C:/Programmieren/wizardrytranslation/tools')
from psmt8_deswizzle import deswizzle_psmt8
from PIL import Image

path = 'C:/Programmieren/wizardrytranslation/extracted/packdata_raw/2138_type29.raw'
data = open(path, 'rb').read()

records = []
for i in range(29):
    rec_off = i * 16
    idx, size, offset, unk = struct.unpack_from('<IIII', data, rec_off)
    records.append((idx, size, offset, unk))

# Try subs 9-11 as PSMT8 256x256 with header=0x4A0
for sub_i in [9, 10, 11, 12, 13]:
    idx, size, offset, unk = records[sub_i]
    abs_pixel = offset + 0x4A0
    pixel_size = 256 * 256
    pdata = bytes(data[abs_pixel:abs_pixel+pixel_size])
    linear = deswizzle_psmt8(pdata, 256, 256, bw_psmt8=256, dbw_ct32=4)
    img = Image.new("L", (256, 256))
    for i, p in enumerate(linear[:256*256]):
        img.putpixel((i % 256, i // 256), p)
    fn = f"C:/Programmieren/wizardrytranslation/build/r2138_sub{sub_i:02d}_psmt8_preview.png"
    img.save(fn)
    print(f"sub{sub_i:02d} PSMT8: saved {fn}")
