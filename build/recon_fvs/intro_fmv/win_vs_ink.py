import sys
sys.stdout.reconfigure(encoding='utf-8')
# window usable px = uvW; JP ink run that occupies it (from page_ink runs).
# Determine usable px per window and px/glyph for english (18px font ~ 9-11px/char)
windows={
0:[(0,72),(96,384)], 1:[(0,312)], 2:[(0,240)], 3:[(0,144),(168,456)],
4:[(0,192),(216,336),(336,432)], 5:[(0,216)], 6:[(0,216)], 7:[(0,312)],
8:[(0,240)], 9:[(0,288)], 10:[(0,336)], 11:[(0,312)], 12:[(0,216)],
13:[(0,336)], 14:[(0,216),(240,384),(384,464)], 15:[(0,312)], 16:[(0,192),(216,504)], 17:[(0,168)]}
# JP ink runs per line (from page_ink.py)
inkruns={
0:[(3,68),(97,257),(268,380)],1:[(9,309)],2:[(2,222)],3:[(1,139),(169,452)],
4:[(4,188),(218,282),(294,426)],5:[(1,198)],6:[(2,212)],7:[(2,295)],
8:[(1,223)],9:[(4,286)],10:[(1,318)],11:[(2,295)],12:[(9,199)],
13:[(1,318)],14:[(1,210),(244,285),(296,358),(369,462)],15:[(1,295)],
16:[(9,486)],17:[(4,167)]}
print(f"{'ln':>2} | windows (uvX0..X1, usableW) | total_usable | JP_inkW")
for i in range(18):
    ws=windows[i]
    parts=[f"[{a}..{b}]u{b-a}" for a,b in ws]
    tot=sum(b-a for a,b in ws)
    inkw=sum(b-a+1 for a,b in inkruns[i])
    print(f"{i:>2} | {'  '.join(parts):45s} | usable={tot:4} | inkW={inkw}")
