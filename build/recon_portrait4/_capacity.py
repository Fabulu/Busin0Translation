import sys
sys.stdout.reconfigure(encoding='utf-8')
# Screenshot 640x480. Native PS2 = 512x448 (standard NTSC interlace for this engine).
# EXE proves: glyph cell = 24x24 native, line PITCH = 24 native (confirmed x24 dest-Y).
# Box interior in screenshot: top y=363, bottom y=473 -> height_ss=110px
# scale_y = 480/448 = 1.07143 -> native box height = 110/1.07143 = 102.7 ~ 103px native
sy=480/448
box_top_ss=363; box_bot_ss=473
box_h_ss=box_bot_ss-box_top_ss
box_h_nat=box_h_ss/sy
print(f"box interior height: screenshot={box_h_ss}px  native={box_h_nat:.1f}px")
pitch_nat=24
print(f"line pitch native = {pitch_nat}px (EXE-proven)")
# Lines that fit: first line baseline starts ~ a few px below top.
# glyph height 24. lines fitting = floor(box_h / pitch)
for pitch in [24,22,21,20,19,18]:
    n=box_h_nat/pitch
    print(f"  pitch={pitch}: lines fitting = {n:.2f}  -> {int(n)} full lines (glyph cell 24 tall: needs cell to fit)")
print()
# A glyph is 24 tall. With pitch P, line i top = top0 + i*P. Last line bottom = top0+(n-1)*P+24 <= box_bot
# Solve n for top0~box_top: (n-1)*P + 24 <= box_h_nat
for pitch in [24,22,21,20,19,18,16]:
    n=1
    while (n)*pitch + (24-pitch) <= box_h_nat:  # last glyph bottom
        n+=1
    n-=1
    # simpler: lines where (i)*pitch+24 <= box_h, i=0..; count
    cnt=0
    i=0
    while i*pitch+24 <= box_h_nat+1:
        cnt+=1; i+=1
    print(f"  pitch={pitch}: full 24px-tall lines that fully fit in {box_h_nat:.0f}px box = {cnt}")
