import sys,json
sys.stdout.reconfigure(encoding='utf-8')
m=json.load(open("C:/programmieren/wizardrytranslation/build/recon_w3/probe/metrics.json"))
IL={r[0]:r[2] for r in m}; IR={r[0]:r[3] for r in m}; W={r[0]:r[4] for r in m}
def gid(ch): return ord(ch)-32

# MODEL 2 chosen. advance[g] = clamp(ink_width + G, lo, hi). space=9 (floor). draw shift = -ink_left.
# Choose G so a normal word space (space adv 9) + the letter side-gaps read as a clear word break.
# With uniform letter gap = G, a SPACE should look like ~2-3 letter-gaps. Pick G=4 (comfortable, avoids collisions, still compact).
G=4
LO=6; HI=23
adv=[0]*95
shift=[0]*95
for g in range(95):
    if g==0:
        adv[g]=9; shift[g]=0; continue
    if W[g]==0:  # blank glyphs like @ \ (gid32,60) - treat as space-ish
        adv[g]=9; shift[g]=0; continue
    a=W[g]+G
    a=max(LO,min(HI,a))
    adv[g]=a
    shift[g]=IL[g] if IL[g]>0 else 0
# avg advance over letters that actually appear in english (a-z, A-Z, common punct)
import string
common=[gid(c) for c in (string.ascii_letters+" ,.")]
avg=sum(adv[g] for g in common)/len(common)
print(f"chosen G={G}, clamp[{LO},{HI}], space=9")
print(f"avg advance over A-Za-z space ,.  = {avg:.2f}px  (vs 18 constant)  => packs {18/avg:.2f}x more chars/line")
# letters only
let=[gid(c) for c in string.ascii_letters]
avgL=sum(adv[g] for g in let)/len(let)
print(f"avg advance letters only = {avgL:.2f}px (vs 18)")

print("\n95-entry ADVANCE table (gid: char adv shift inkW inkL):")
for g in range(95):
    print("%3d %r  adv=%2d shift=%2d  (W=%2d L=%2d)"%(g,chr(g+32),adv[g],shift[g],W[g],IL[g]))

print("\nADVANCE_BYTES =", adv)
print("\nLEFTSHIFT_BYTES =", shift)
json.dump({"advance":adv,"leftshift":shift,"G":G,"model":2}, open("C:/programmieren/wizardrytranslation/build/recon_w3/probe/advance_table.json","w"))
