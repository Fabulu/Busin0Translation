import sys
sys.stdout.reconfigure(encoding='utf-8')
# Compare JP ink position WITHIN each engine UV window: left-aligned, centered, or full?
# windows from correlate/exact_windows; JP ink runs from page_ink.
windows={
 0:[(0,72),(96,384)],
 1:[(0,312)],2:[(0,240)],
 3:[(0,144),(168,456)],
 4:[(0,192),(216,336),(336,432)],
 5:[(0,216)],6:[(0,216)],7:[(0,312)],8:[(0,240)],9:[(0,288)],
 10:[(0,336)],11:[(0,312)],12:[(0,216)],13:[(0,336)],
 14:[(0,216),(240,384),(384,464)],15:[(0,312)],
 16:[(0,192),(216,504)],17:[(0,168)]}
# JP ink full extent per line (inkX min..max) from page_ink
inkext={0:(3,380),1:(9,309),2:(2,222),3:(1,452),4:(4,426),5:(1,198),6:(2,212),
 7:(2,295),8:(1,223),9:(4,286),10:(1,318),11:(2,295),12:(9,199),13:(1,318),
 14:(1,462),15:(1,295),16:(9,486),17:(4,167)}
# per-line JP runs (page_ink) to see ink inside each window
runs={
0:[(3,68),(97,257),(268,380)],1:[(9,19),(30,309)],2:[(2,222)],3:[(1,139),(169,452)],
4:[(4,188),(218,282),(294,426)],5:[(1,198)],6:[(2,212)],7:[(2,295)],8:[(1,137),(148,223)],
9:[(4,19),(30,67),(78,286)],10:[(1,318)],11:[(2,295)],12:[(9,19),(30,199)],13:[(1,283),(294,318)],
14:[(1,210),(244,285),(296,358),(369,462)],15:[(1,295)],16:[(9,19),(30,189),(217,486)],17:[(4,167)]}

print("For each engine window: JP ink left-margin vs right-margin (within window)")
for i,wins in windows.items():
    lr=runs[i]
    for (wx0,wx1) in wins:
        # ink columns inside this window
        ink_in=[(max(a,wx0),min(b,wx1)) for a,b in lr if not(b<wx0 or a>wx1)]
        if not ink_in:
            print(f" line{i:2} win[{wx0},{wx1}] : (no ink)"); continue
        imin=min(a for a,b in ink_in); imax=max(b for a,b in ink_in)
        lm=imin-wx0; rm=wx1-imax
        tag="LEFT" if lm<rm-12 else ("RIGHT" if rm<lm-12 else "CENTERED/FULL")
        print(f" line{i:2} win[{wx0:3},{wx1:3}]w{wx1-wx0:3} : ink[{imin:3}..{imax:3}] Lmarg={lm:3} Rmarg={rm:3}  -> {tag}")
