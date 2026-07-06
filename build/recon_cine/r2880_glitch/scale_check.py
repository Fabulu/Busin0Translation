import sys, json, os
sys.stdout.reconfigure(encoding='utf-8')
BASE="C:/programmieren/wizardrytranslation"
sys.path.insert(0, os.path.join(BASE,"tools"))
from strip_patcher import load_font

# GS-observed destination rects per (line, uvWindow): from center_check.py
gs = {
 0:[((0,72),(217.6,300.7)),((96,384),(82.4,436.0))],
 3:[((0,144),(177.9,340.3)),((168,456),(106.4,427.2))],
 4:[((0,192),(138.7,374.9)),((216,336),(116.0,277.0)),((336,432),(276.9,406.6))],
 14:[((0,216),(140.6,382.1)),((240,384),(140.6,302.9)),((384,464),(296.7,388.7))],
 16:[((0,192),(149.4,364.5)),((216,504),(105.4,426.1))],
}
cfg=json.load(open(os.path.join(BASE,"data/strip_labels/r2880_prologue.json"),encoding="utf-8"))
font=load_font(18,bold=True)
left_pad=cfg["layout"]["left_pad"]

print("=== For each JSON seg: where does its INK land on screen? ===")
print("(engine stretches the WHOLE uv-window to its dest rect; we author ink left-aligned at win.x0+left_pad)")
for i,ln in enumerate(cfg["lines"]):
    if i not in gs: continue
    print(f"\nline {i}: JSON windows={ln['windows']} segs={ln['segs']}")
    # map JSON window -> which GS sub-windows it spans
    for (jx0,jx1),text in zip(ln["windows"],ln["segs"]):
        bb=font.getbbox(text); tw=bb[2]-bb[0]
        ink_x0=jx0+left_pad           # left edge of ink in texel space
        ink_x1=ink_x0+tw              # right edge of ink in texel space
        # find GS sub-windows overlapping [jx0,jx1]
        subs=[(u,d) for (u,d) in gs[i] if not(u[1]<=jx0 or u[0]>=jx1)]
        # build piecewise texel->screen map from subs
        def tex2scr(tx):
            for (u0,u1),(d0,d1) in subs:
                if u0<=tx<=u1:
                    return d0+(tx-u0)/(u1-u0)*(d1-d0)
            # clamp to nearest
            (u0,u1),(d0,d1)=subs[0]
            return d0+(tx-u0)/(u1-u0)*(d1-d0)
        s0=tex2scr(ink_x0); s1=tex2scr(ink_x1)
        # dest extent of the whole json window
        wd0=tex2scr(jx0); wd1=tex2scr(min(jx1,subs[-1][0][1]))
        ink_ctr=(s0+s1)/2; win_ctr=(wd0+wd1)/2
        print(f"  seg '{text}' tw={tw}tex  ink_screen[{s0:.0f}..{s1:.0f}]w{s1-s0:.0f}  "
              f"winDest[{wd0:.0f}..{wd1:.0f}]  ink_ctr={ink_ctr:.0f} winDest_ctr={win_ctr:.0f} "
              f"offset_from_winctr={ink_ctr-win_ctr:+.0f}px")
        # check for scale discontinuity crossed by ink
        if len(subs)>1:
            for k in range(len(subs)-1):
                boundary=subs[k][0][1]
                if ink_x0<boundary<ink_x1:
                    sc0=(subs[k][1][1]-subs[k][1][0])/(subs[k][0][1]-subs[k][0][0])
                    sc1=(subs[k+1][1][1]-subs[k+1][1][0])/(subs[k+1][0][1]-subs[k+1][0][0])
                    print(f"    !! ink crosses sub-window boundary at texel {boundary}: "
                          f"scale {sc0:.3f}->{sc1:.3f} (text gets stretched discontinuously)")
