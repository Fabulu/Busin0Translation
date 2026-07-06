import sys
sys.stdout.reconfigure(encoding='utf-8')
# screenshot 640x480. PS2 likely renders 512x448 or 640x448 then scaled to 4:3.
# If native height 448 -> 480: scale_y = 480/448 = 1.0714
# dialogue pitch in screenshot = 26.0 px
for nativeH in [448,416,480,512]:
    sy=480.0/nativeH
    print(f"nativeH={nativeH} scale_y={sy:.4f} -> dialogue pitch native={26.0/sy:.2f}px  narration native={25.6/sy:.2f}px")
print()
# Box geometry: ladyknight line1 top glyph y0=387(screenshot). last line bottom ~473. name banner ~332-345.
# Convert box region:
print("ladyknight dialogue region screenshot: line1 top=387, line4 bottom~473 -> span=86px /scale")
for nativeH in [448,416]:
    sy=480.0/nativeH
    print(f"  nativeH={nativeH}: line1 top native={387/sy:.0f}, line4 bottom native={473/sy:.0f}, span={86/sy:.0f}")
