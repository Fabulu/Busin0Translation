import sys
sys.stdout.reconfigure(encoding='utf-8')
sy=480/448  # 1.07143
# ladyknight: box top border ss=363, bottom ss=473 => interior height ss=110, native=102.7
# line glyph tops (ss): L1=387, L2=413, L3=440, L4=465  (from band y0)
# convert tops to native and relative to box-top
box_top=363
tops_ss=[387,413,440,465]
print("ladyknight line tops relative to box top (native):")
for i,t in enumerate(tops_ss):
    rel_ss=t-box_top
    print(f"  L{i+1}: ss_rel={rel_ss}  native_rel={rel_ss/sy:.1f}")
# pitch between tops native:
pitches=[(tops_ss[i+1]-tops_ss[i])/sy for i in range(3)]
print("measured native pitches:", [round(p,1) for p in pitches], "avg", round(sum(pitches)/3,1))
# top padding = native_rel of L1
pad_top=(tops_ss[0]-box_top)/sy
print(f"top padding (box_top to L1 glyph top) native = {pad_top:.1f}")
# box interior native
box_h=(473-363)/sy
print(f"box interior height native = {box_h:.1f}")
print()
# Capacity model: last glyph bottom must be <= box_bottom.
# line i top = pad_top + i*pitch ; bottom = that+24.  Fit if pad_top+(n-1)*pitch+24 <= box_h
for pitch in [24,21,20,19,18,17]:
    n=0
    while pad_top+n*pitch+24 <= box_h+1.5:  # small tolerance
        n+=1
    print(f"  pitch={pitch}: fits {n} lines (pad_top={pad_top:.0f}, box_h={box_h:.0f})")
print()
# To fit 5 lines: need pad_top+4*pitch+24 <= box_h => pitch <= (box_h-24-pad_top)/4
maxpitch5=(box_h-24-pad_top)/4
print(f"max pitch to fit 5 lines = {maxpitch5:.2f} native")
maxpitch4=(box_h-24-pad_top)/3
print(f"max pitch to fit 4 lines = {maxpitch4:.2f} native (current 24 already ~marginal)")
