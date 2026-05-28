import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
with open("C:/Programmieren/wizardrytranslation/dumps/guide_full.txt","r",encoding="latin-1") as f:
    text = f.read()
print(f"Guide size: {len(text)} chars")
keywords = ["??","??","??","??","??","??","??","???","??","??","?","???","????","????"]
for kw in keywords:
    positions = [m.start() for m in re.finditer(kw, text)]
    if positions:
        print(f"{kw}: found {len(positions)} times")
        for p in positions[:3]:
            ctx = text[max(0,p-30):p+50]
            print(f"  ...{repr(ctx)}...")
    else:
        print(f"{kw}: not found")

