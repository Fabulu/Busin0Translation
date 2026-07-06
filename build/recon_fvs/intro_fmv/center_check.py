import sys
sys.stdout.reconfigure(encoding='utf-8')
# For each window: dest center vs uv width. Test hypothesis: dest is centered on
# a fixed screen X for the whole LINE, with each window placed at its texel offset.
rows = {
 0:[((0,72),(217.6,300.7)),((96,384),(82.4,436.0))],
 3:[((0,144),(177.9,340.3)),((168,456),(106.4,427.2))],
 4:[((0,192),(138.7,374.9)),((216,336),(116.0,277.0)),((336,432),(276.9,406.6))],
 14:[((0,216),(140.6,382.1)),((240,384),(140.6,302.9)),((384,464),(296.7,388.7))],
 16:[((0,192),(149.4,364.5)),((216,504),(105.4,426.1))],
}
for li,wins in rows.items():
    print(f"line {li}:")
    for (u0,u1),(dx0,dx1) in wins:
        uvw=u1-u0; dw=dx1-dx0
        scale=dw/uvw if uvw else 0
        # if window placed at uv offset from a line-anchor screen X:
        # screen_x_of_texel0 = dx0 - u0*scale
        anchor = dx0 - u0*scale
        print(f"   uv[{u0:3}..{u1:3}]w{uvw:3} dest[{dx0:6.1f}..{dx1:6.1f}]w{dw:6.1f} scale={scale:.3f} texel0_screenX={anchor:7.2f} center={(dx0+dx1)/2:7.2f}")
