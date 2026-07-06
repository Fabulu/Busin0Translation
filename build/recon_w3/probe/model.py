import sys,json
sys.stdout.reconfigure(encoding='utf-8')
m=json.load(open("C:/programmieren/wizardrytranslation/build/recon_w3/probe/metrics.json"))
IL={r[0]:r[2] for r in m}; IR={r[0]:r[3] for r in m}; W={r[0]:r[4] for r in m}
def gid(ch): return ord(ch)-32
text="A heavy fog had settled over the deserted streets."

# --- MODEL 1: advance = ink_right_edge + G, no draw shift, space floor ---
def sim(model, G, space_adv):
    xs=[]; x=0.0
    for ch in text:
        g=gid(ch); xs.append((ch,g,x))
        if g==0: x+=space_adv; continue
        if model==1:
            adv=(IR[g]+1)+G
        elif model==2:
            adv=W[g]+G
        adv=max(6,min(23,adv))
        x+=adv
    return xs

def gaps(xs, model):
    out=[]
    for i in range(len(xs)-1):
        ch,g,xo=xs[i]; ch2,g2,xo2=xs[i+1]
        if g==0 or g2==0: continue
        if IR[g]<0 or IL[g2]<0: continue
        # draw origin: model1 draws at cell origin xo (ink at xo+IL); model2 draws at xo-IL (ink flush at xo)
        if model==1:
            inkR_abs = xo+IR[g]+1; inkL_abs = xo2+IL[g2]
        else:
            inkR_abs = xo+W[g]; inkL_abs = xo2  # flush
        out.append((f"{ch}->{ch2}", inkL_abs-inkR_abs))
    return out

import statistics as st
for model,G,sa,label in [(1,2,9,"M1 advance=inkR+2"),(2,3,9,"M2 advance=inkW+3 +draw-shift")]:
    xs=sim(model,G,sa)
    gp=gaps(xs,model)
    vals=[v for _,v in gp]
    print(f"\n=== {label} ===")
    print(f"  total width={xs[-1][2]:.0f}  vs current 18*~ ({len(text)} chars)")
    print(f"  gap min={min(vals)} max={max(vals)} mean={st.mean(vals):.1f} stdev={st.pstdev(vals):.2f}")
