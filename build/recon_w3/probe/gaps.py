import sys,json
sys.stdout.reconfigure(encoding='utf-8')
m=json.load(open("C:/programmieren/wizardrytranslation/build/recon_w3/probe/metrics.json"))
IL={r[0]:r[2] for r in m}; IR={r[0]:r[3] for r in m}; W={r[0]:r[4] for r in m}
def gid(ch): return ord(ch)-32
# current build: cell origin advance: 18 per glyph, but space cell advances 9.
# Reconstruct origins for "A heavy fog had" exactly like the screen (start x=99 for A cell-left? screen showed x as bottom-right vertex=cell right; cell origin = x-? Actually delta=18 cell-to-cell so treat x as origin)
text="A heavy fog had settled over the deserted streets."
# advance rule current: space->9, else 18
xs=[]; x=0.0
for ch in text:
    g=gid(ch); xs.append((ch,g,x))
    x += 9 if g==0 else 18
print("CURRENT build visible gaps (edge of ink to next ink):")
for i in range(len(xs)-1):
    ch,g,xo=xs[i]; ch2,g2,xo2=xs[i+1]
    if g==0 or g2==0: continue  # skip space-involved for letter pairs
    if IR[g]<0 or IL[g2]<0: continue
    gap=(xo2+IL[g2])-(xo+IR[g]+1)  # +1: ink_right is last inked col, edge at +1
    print(f"  '{ch}'->'{ch2}': gap={gap:.1f}px")
