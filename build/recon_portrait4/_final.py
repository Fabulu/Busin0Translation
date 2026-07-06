import sys
sys.stdout.reconfigure(encoding='utf-8')
sy=480/448
box_h=(473-363)/sy   # 102.7 native interior
pad_top=(387-363)/sy # 22.4 native (box top -> first glyph top)
ink=10               # native ink height (measured 7-12)
print(f"box interior height = {box_h:.0f}px native ; top pad = {pad_top:.0f}px ; ink height ~{ink}px")
print()
print("Lines that fit (last line's INK must stay above box bottom):")
for pitch in [24,20,19,18,17,16]:
    # line i ink-top = pad_top + i*pitch ; ink-bottom = +ink. Fit if ink-bottom <= box_h
    n=0
    while pad_top + n*pitch + ink <= box_h+1:
        n+=1
    # also: full 24px cell fit (stricter, cell bottom <= box_h)
    nc=0
    while pad_top + nc*pitch + 24 <= box_h+2:
        nc+=1
    print(f"  pitch={pitch}: ink-fit={n} lines | full-cell-fit={nc} lines")
