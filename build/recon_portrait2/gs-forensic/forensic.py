#!/usr/bin/env python3
"""Hardware-level portrait forensic: PRESENT vs ABSENT GS dump classification.

For each dump:
  (1) Enumerate every host->VRAM BITBLT; flag R1251-sourced ones (the portrait
      128x256 PSMCT32 -> dbp=0x3000 + 16x16 CLUT -> dbp=0x3200/CBP=0x200D0 region).
  (2) Snapshot the dbp=0x3000 region (PSMT8 256x512 portrait address space) and
      report what resource currently occupies it after all transfers applied.
  (3) Enumerate textured DRAWS that sample TBP0=0x3000 (portrait slot) regardless
      of which texture is actually there -> tells us if the draw exists.
  (4) Characterize the portrait SCREEN RECT in PRESENT, then check ABSENT for any
      draw to that same rect (sampling ANY texture).
"""
import sys, os, hashlib
sys.path.insert(0, 'C:/programmieren/wizardrytranslation/build/recon_v86/gs-vram-atlas')
import gs_atlas as G
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')

RAW = 'C:/programmieren/wizardrytranslation/extracted/packdata_raw'
R1251 = open(f'{RAW}/1251_type01.raw', 'rb').read()
R1188 = open(f'{RAW}/1188_type01.raw', 'rb').read()
SNAPS = G.SNAPS

# portrait payload = R1251 + 0xA1 ; CLUT = R1251 + 0x200D0
PORTRAIT_SRC = R1251[0xA1:0xA1 + 128*256*4]      # 128x256 PSMCT32
CLUT_SRC = R1251[0x200D0:0x200D0 + 16*16*4]      # 16x16 CLUT cells (256 entries CT32)

def src_match(data, names=('1251','1250','1252','1253','1188','1191','1252')):
    if len(data) < 64:
        return None
    needle = bytes(data[:256])
    for name in names:
        try:
            blob = open(f'{RAW}/{name}_type01.raw', 'rb').read()
        except FileNotFoundError:
            continue
        idx = blob.find(needle)
        if idx >= 0:
            return (name, idx, len(data))
    return None

def analyze(ts, label):
    path = SNAPS + f'/Busin 0 - Wizardry Alternative Neo_SLPM-65378_{ts}.gs.zst'
    if not os.path.exists(path):
        print(f"\n##### MISSING DUMP {label} {ts}")
        return None
    vram, draws, transfers, frames = G.parse_dump(path)
    print(f"\n================ {label}  {ts} ================")
    print(f"transfers={len(transfers)} draws={len(draws)} frames(FB)={sorted(frames)}")

    # ---- (1) BITBLT enumeration: R1251 + dest near 0x3000/0x3200 ----
    r1251_tx = []
    dest3000 = []
    for i, t in enumerate(transfers):
        sm = src_match(t['data'])
        d = bytes(t['data'])
        is_portrait = (d[:len(PORTRAIT_SRC)] == PORTRAIT_SRC) if len(d) >= len(PORTRAIT_SRC) else False
        is_clut = (len(d) >= 64 and d[:64] == CLUT_SRC[:64])
        psm = G.PSM_NAMES.get(t['dpsm'], hex(t['dpsm']))
        if sm and sm[0] == '1251':
            r1251_tx.append(i)
            print(f"  [R1251 TX {i}] dbp=0x{t['dbp']:04X} {psm} {t['rrw']}x{t['rrh']} "
                  f"({len(d)}B) src=1251+0x{sm[1]:X} portraitExact={is_portrait} clutExact={is_clut}")
        # any transfer landing in the 0x3000..0x33FF dest window
        if 0x3000 <= t['dbp'] <= 0x3400:
            srcname = sm[0]+f"+0x{sm[1]:X}" if sm else "?"
            dest3000.append((i, t['dbp'], psm, t['rrw'], t['rrh'], len(d), srcname))
    print(f"  >>> R1251-sourced transfers: {len(r1251_tx)} (indices {r1251_tx})")
    print(f"  >>> transfers landing dbp in [0x3000..0x3400]: {len(dest3000)}")
    for i, dbp, psm, w, h, n, sn in dest3000[:20]:
        print(f"       TX{i} dbp=0x{dbp:04X} {psm} {w}x{h} {n}B src={sn}")

    # ---- (2) dbp=0x3000 region content snapshot ----
    # Read it as PSMT8 256x512 (portrait native) and CT32, hash to see what's there.
    base = 0x3000 * 256
    region = vram[base:base + 256*512]  # raw bytes in that VRAM byte-range
    nonzero = int(np.count_nonzero(region))
    # match the raw VRAM bytes against R1251 portrait payload + R1188 font
    reg_bytes = region.tobytes()
    h3000 = hashlib.md5(reg_bytes[:0x8000]).hexdigest()[:12]
    # Does the portrait payload appear anywhere in the 0x3000 region's source-equivalent?
    print(f"  >>> dbp=0x3000 region: nonzero={nonzero}/{len(region)} md5[:0x8000]={h3000}")

    # ---- (3) draws sampling TBP0=0x3000 ----
    portrait_slot_draws = []
    for d in draws:
        t = d['tex0']
        if t['tbp0'] == 0x3000:
            ox, oy = d['xyoff']
            xs = [(v[0]-ox)/16.0 for v in d['verts']]
            ys = [(v[1]-oy)/16.0 for v in d['verts']]
            rect = (round(min(xs)), round(min(ys)), round(max(xs)), round(max(ys))) if xs else None
            portrait_slot_draws.append((d['seq'], G.PSM_NAMES.get(t['psm'], hex(t['psm'])),
                                        t['tw'], t['th'], f"0x{t['cbp']:04X}", rect))
    print(f"  >>> DRAWS sampling TBP0=0x3000: {len(portrait_slot_draws)}")
    seen = set()
    for seq, psm, tw, th, cbp, rect in portrait_slot_draws:
        k = (psm, tw, th, cbp, rect)
        if k in seen:
            continue
        seen.add(k)
        print(f"       draw seq={seq} {psm} tex={tw}x{th} cbp={cbp} screenRect={rect}")

    # ---- (4) all distinct textured-draw screen rects (to find portrait rect) ----
    rects = {}
    for d in draws:
        t = d['tex0']
        ox, oy = d['xyoff']
        xs = [(v[0]-ox)/16.0 for v in d['verts']]
        ys = [(v[1]-oy)/16.0 for v in d['verts']]
        if not xs:
            continue
        rect = (round(min(xs)), round(min(ys)), round(max(xs)), round(max(ys)))
        w = rect[2]-rect[0]; hgt = rect[3]-rect[1]
        # portrait is ~128 wide x ~256 tall on screen
        if 40 <= w <= 200 and 100 <= hgt <= 320:
            key = rect
            e = rects.setdefault(key, {'count':0,'tbps':set()})
            e['count'] += 1
            e['tbps'].add((t['tbp0'], G.PSM_NAMES.get(t['psm'],hex(t['psm']))))
    print(f"  >>> portrait-sized draw rects (w 40-200, h 100-320): {len(rects)}")
    for rect, e in sorted(rects.items(), key=lambda kv: -kv[1]['count'])[:12]:
        tbps = ", ".join(f"0x{tb:04X}:{ps}" for tb,ps in sorted(e['tbps']))
        print(f"       rect={rect} count={e['count']} sampledFrom=[{tbps}]")

    return {'ts':ts,'label':label,'n_tx':len(transfers),'n_draws':len(draws),
            'r1251_tx':len(r1251_tx),'dest3000':len(dest3000),
            'slot3000_draws':len(portrait_slot_draws),'h3000':h3000,'nonzero':nonzero}

PAIRS = [
    ('20260611203408','PRESENT  JP-ref Simzon'),
    ('20260613170106','ABSENT   v89 Sister/bar dialogue A'),
    ('20260613171306','ABSENT   v89 dialogue B'),
    ('20260613103826','ABSENT   v86 Simzon'),
]

if __name__ == '__main__':
    print(f"PORTRAIT_SRC len={len(PORTRAIT_SRC)} first8={PORTRAIT_SRC[:8].hex()}")
    print(f"CLUT_SRC len={len(CLUT_SRC)} first8={CLUT_SRC[:8].hex()}")
    rows = []
    for ts, lab in PAIRS:
        r = analyze(ts, lab)
        if r: rows.append(r)
    print("\n\n==== SUMMARY ====")
    print(f"{'label':40s} {'tx':>5} {'draws':>6} {'R1251tx':>8} {'dest3000':>9} {'slot3000draws':>14}")
    for r in rows:
        print(f"{r['label']:40s} {r['n_tx']:>5} {r['n_draws']:>6} {r['r1251_tx']:>8} {r['dest3000']:>9} {r['slot3000_draws']:>14}  h3000={r['h3000']}")
