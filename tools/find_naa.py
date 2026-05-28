import struct, os, json

RESDIR = "C:/Programmieren/wizardrytranslation/extracted/packdata_resources"
with open("C:/Programmieren/wizardrytranslation/dumps/resource_classification.json") as f:
    cls = json.load(f)
msg_indices = cls["msg_resource_indices"]

files = os.listdir(RESDIR)
fmap = {}
for f in files:
    try:
        fmap[int(f[:4])] = os.path.join(RESDIR, f)
    except:
        pass

for idx in msg_indices:
    if idx not in fmap:
        continue
    with open(fmap[idx], "rb") as fh:
        data = fh.read()
    for off in range(0, len(data) - 3, 2):
        a = struct.unpack(">H", data[off:off+2])[0]
        b = struct.unpack(">H", data[off+2:off+4])[0]
        if a == 132 and b == 112:
            # Found! Show context (50 bytes before and after)
            start = max(0, off - 40)
            end = min(len(data), off + 80)
            context = []
            for p in range(start, end - 1, 2):
                v = struct.unpack(">H", data[p:p+2])[0]
                if p == off:
                    context.append("*%d*" % v)
                elif p == off + 2:
                    context.append("*%d*" % v)
                else:
                    context.append(str(v))
            print("res=%d off=0x%X" % (idx, off))
            print("  context: [%s]" % ", ".join(context))
            
            # Find surrounding FFFF boundaries
            ffff_before = off
            while ffff_before > 0:
                v = struct.unpack(">H", data[ffff_before:ffff_before+2])[0]
                if v == 0xFFFF:
                    break
                ffff_before -= 2
            ffff_after = off + 4
            while ffff_after < len(data) - 1:
                v = struct.unpack(">H", data[ffff_after:ffff_after+2])[0]
                if v == 0xFFFF:
                    break
                ffff_after += 2
            
            # Extract message
            msg = []
            for p in range(ffff_before + 2, ffff_after, 2):
                v = struct.unpack(">H", data[p:p+2])[0]
                msg.append(v)
            tg = [g for g in msg if g < 0xFFC0]
            print("  message glyphs: %s" % msg)
            print("  text only: %s" % tg)
            print()

print("DONE")
