import sys,json,string,statistics as st
sys.stdout.reconfigure(encoding='utf-8')
m=json.load(open("C:/programmieren/wizardrytranslation/build/recon_w3/probe/metrics.json"))
IL={r[0]:r[2] for r in m}; IR={r[0]:r[3] for r in m}; W={r[0]:r[4] for r in m}
def gid(c): return ord(c)-32
G=3; LO=6; HI=23
adv=[0]*95; shift=[0]*95
for g in range(95):
    if g==0 or W[g]==0:
        adv[g]=9; shift[g]=0
    else:
        adv[g]=max(LO,min(HI,W[g]+G))
        shift[g]=max(0,IL[g])
# simulate full sentence, MODEL 2 (draw at penX - shift, ink flush at penX, width=ink_width unless clamped)
text="A heavy fog had settled over the deserted streets."
x=0.0; pos=[]
for ch in text:
    g=gid(ch); pos.append((ch,g,x)); x+=adv[g]
gaps=[]
for i in range(len(pos)-1):
    ch,g,xo=pos[i]; ch2,g2,xo2=pos[i+1]
    if g==0 or g2==0: continue
    if W[g]==0 or W[g2]==0: continue
    inkR = xo + W[g]          # flush draw: ink occupies [xo, xo+W)
    inkL = xo2                # next ink flush at its origin
    gaps.append(inkL-inkR)
print(f"G={G} MODEL2 full-sentence inter-letter gaps: min={min(gaps)} max={max(gaps)} mean={st.mean(gaps):.2f} stdev={st.pstdev(gaps):.3f}")
print("note: gap==G for all unclamped glyphs; clamped wide glyphs (W+G>23) give gap slightly < G")
# how many clamped
clamped=[g for g in range(95) if W[g]>0 and W[g]+G>23]
print("clamped glyphs (W+3>23):", [chr(g+32) for g in clamped])
print("\nFINAL G=3 ADVANCE =", adv)
print("\nFINAL G=3 LEFTSHIFT =", shift)
json.dump({"G":3,"model":2,"advance":adv,"leftshift":shift},open("C:/programmieren/wizardrytranslation/build/recon_w3/probe/advance_table_G3.json","w"))
