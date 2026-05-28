import struct, os

RESDIR = "C:/Programmieren/wizardrytranslation/extracted/packdata_resources"

def dump_resource(idx):
    for f in os.listdir(RESDIR):
        if f.startswith("%04d_" % idx):
            path = os.path.join(RESDIR, f)
            break
    else:
        print("Not found: %d" % idx)
        return
    with open(path, "rb") as fh:
        data = fh.read()
    
    print("=== Resource %d: %d bytes ===" % (idx, len(data)))
    
    # Extract all FFFF-delimited sequences, keeping FFFE inline
    i = 0
    sn = 0
    while i < len(data) - 1:
        val = struct.unpack(">H", data[i:i+2])[0]
        if val == 0xFFFF:
            gl = []
            j = i + 2
            while j < len(data) - 1:
                g = struct.unpack(">H", data[j:j+2])[0]
                if g == 0xFFFF:
                    break
                gl.append(g)
                j += 2
            tg = [g for g in gl if g < 0xFF00]
            ctrls = [g for g in gl if g >= 0xFF00]
            fffe_count = gl.count(0xFFFE)
            print("  s[%d] off=0x%X tlen=%d fffe=%d gl=%s" % (sn, i, len(tg), fffe_count, gl))
            sn += 1
            i = j
        else:
            i += 2
    print("  Total sequences: %d" % sn)

for idx in [41, 42, 43, 44]:
    dump_resource(idx)
    print()
