import sys,json,string
sys.stdout.reconfigure(encoding='utf-8')
m=json.load(open("C:/programmieren/wizardrytranslation/build/recon_w3/probe/metrics.json"))
IL={r[0]:r[2] for r in m}; IR={r[0]:r[3] for r in m}; W={r[0]:r[4] for r in m}
def gid(c): return ord(c)-32
text="A heavy fog had settled over the deserted streets."
let=[gid(c) for c in string.ascii_letters]
def adv_for(g,G,LO,HI):
    if g==0 or W[g]==0: return 9
    return max(LO,min(HI,W[g]+G))
for G in [2,3,4]:
    a={g:adv_for(g,G,6,23) for g in range(95)}
    avgL=sum(a[g] for g in let)/len(let)
    # render text width
    x=0
    for ch in text: x+=a[gid(ch)]
    cur=0
    for ch in text: cur+= 9 if gid(ch)==0 else 18
    print(f"G={G}: avg letter adv={avgL:.2f}  line '{text}' width={x} vs current {cur}  ({cur/x*100-100:+.0f}% room) space=9 letter-gap={G}")
