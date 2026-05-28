import struct, os

RESDIR = "C:/Programmieren/wizardrytranslation/extracted/packdata_resources"

for f in os.listdir(RESDIR):
    if f.startswith("0046_"):
        with open(os.path.join(RESDIR, f), "rb") as fh:
            data = fh.read()
        break

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
        tg = [g for g in gl if g < 0xFFC0]
        c132 = tg.count(132)
        if c132 >= 4:
            print("s[%d] off=0x%X tlen=%d c132=%d" % (sn, i, len(tg), c132))
            # Show parts
            parts = []
            cur = []
            for g in gl:
                if g == 0xFFFE:
                    parts.append(cur)
                    cur = []
                else:
                    cur.append(g)
            if cur:
                parts.append(cur)
            for pi, p in enumerate(parts):
                txt = [g for g in p if g < 0xFFC0]
                if txt:
                    # Mark positions of 132
                    marked = []
                    for g in txt:
                        if g == 132:
                            marked.append("*%d*" % g)
                        else:
                            marked.append(str(g))
                    print("    p[%d]: [%s]" % (pi, ", ".join(marked)))
        sn += 1
        i = j
    else:
        i += 2

print("DONE")
