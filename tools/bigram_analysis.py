import struct, os, json
from collections import Counter

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

# Count bigrams in resources 34-49
bigrams = Counter()
for idx in range(34, 50):
    if idx not in fmap:
        continue
    with open(fmap[idx], "rb") as fh:
        data = fh.read()
    i = 0
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
            tg = [g for g in gl if 5 <= g < 0xFFC0]
            for k in range(len(tg)-1):
                bigrams[(tg[k], tg[k+1])] += 1
            i = j
        else:
            i += 2

# Show top 50 bigrams
print("Top 50 bigrams (resources 34-49):")
for (a, b), cnt in bigrams.most_common(50):
    print("  (%d, %d) = %d" % (a, b, cnt))

# Show bigrams involving glyph 113 (hypothesized as a common hiragana)
print()
print("Bigrams with 113 as first element (top 15):")
g113_first = [(b, c) for (a, b), c in bigrams.items() if a == 113]
g113_first.sort(key=lambda x: -x[1])
for b, c in g113_first[:15]:
    print("  (113, %d) = %d" % (b, c))

print()
print("Bigrams with 113 as second element (top 15):")
g113_second = [(a, c) for (a, b), c in bigrams.items() if b == 113]
g113_second.sort(key=lambda x: -x[1])
for a, c in g113_second[:15]:
    print("  (%d, 113) = %d" % (a, c))

# Check "ない" pattern: if な=132, い=113 -> (132, 113) count
# And "ている" -> if て=130, い=113 -> (130, 113)? No, ている = て-い-る
# Actually ない = な-い: (132, 113)?
print()
print("Checking specific bigrams for hypothesis testing:")
for a, b, desc in [(132, 113, "na-i?"), (130, 113, "te-i?"), (123, 130, "shi-te?"),
                     (113, 136, "i-no?"), (136, 113, "no-i?"),
                     (132, 113, "na-i"), (117, 150, "ka-ru?"),
                     (113, 117, "?-?"), (136, 117, "?-?"),
                     (113, 63, "?-W"), (113, 31, "?-?")]:
    cnt = bigrams.get((a, b), 0)
    print("  (%d, %d) [%s] = %d" % (a, b, desc, cnt))

print("DONE")
