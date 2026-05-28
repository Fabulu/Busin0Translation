import struct, os
RESDIR = r"C:/Programmieren/wizardrytranslation/extracted/packdata_resources"
path = os.path.join(RESDIR, "0038_type01.bin")
with open(path, "rb") as f:
    data = f.read()
mc = 0
i = 0
all_gl = []
while i < len(data)-1:
    v = struct.unpack(">H", data[i:i+2])[0]
    if v == 0xFFFF:
        mc += 1
        j = i + 2
        gl = []
        while j < len(data)-1:
            vv = struct.unpack(">H", data[j:j+2])[0]
            if vv == 0xFFFF:
                break
            gl.append(vv)
            j += 2
        real_gl = [g for g in gl if g != 0xFFFE]
        all_gl.extend(real_gl)
        if len(real_gl) >= 25:
            print("MSG %d (%d glyphs): %s" % (mc, len(real_gl), str(real_gl)))
        i = j
    else:
        i += 2
print("Total messages: " + str(mc))
if all_gl:
    print("Min glyph: %d, Max glyph: %d" % (min(all_gl), max(all_gl)))

