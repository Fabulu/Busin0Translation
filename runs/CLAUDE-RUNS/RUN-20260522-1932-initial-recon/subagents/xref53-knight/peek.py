import struct, os
RESDIR = r"C:/Programmieren/wizardrytranslation/extracted/packdata_resources"
path = os.path.join(RESDIR, "0038_type01.bin")
with open(path, "rb") as f:
    data = f.read()
print("Size: " + str(len(data)))
for i in range(0, len(data)-1, 2):
    v = struct.unpack(">H", data[i:i+2])[0]
    if v == 0xFFFF:
        print("First FFFF at offset: " + hex(i))
        mc = 0
        j = i
        while j < len(data)-1 and mc < 5:
            v2 = struct.unpack(">H", data[j:j+2])[0]
            if v2 == 0xFFFF:
                mc += 1
                k = j + 2
                gl = []
                while k < len(data)-1:
                    vv = struct.unpack(">H", data[k:k+2])[0]
                    if vv == 0xFFFF:
                        break
                    gl.append(vv)
                    k += 2
                print("MSG %d (%d glyphs): %s" % (mc, len(gl), str(gl[:40])))
                j = k
            else:
                j += 2
        break

