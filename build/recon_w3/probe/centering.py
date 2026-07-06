import sys,json
sys.stdout.reconfigure(encoding='utf-8')
t=json.load(open("C:/programmieren/wizardrytranslation/build/recon_w3/probe/advance_table_G3.json"))
adv=t['advance']
def gid(c): return ord(c)-32
lines=["A heavy fog had","settled over the","deserted","streets."]
print("Per-line: true summed advance vs count*K approximations")
for ln in lines:
    n=len(ln)
    real=sum(adv[gid(c)] for c in ln)
    print(f"  '{ln}' count={n} realW={real}  count*18={n*18}(err {n*18-real:+d})  count*17={n*17}(err {n*17-real:+d})  count*16={n*16}(err {n*16-real:+d})")
    print(f"     centering drift if reserve count*18: line shifts {(n*18-real)/2:+.1f}px from true-center")
