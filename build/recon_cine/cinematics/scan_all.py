#!/usr/bin/env python3
"""Scan ALL sheet-container resources for inverted-ramp PSMT4 baked-text
pages (bg=15 dominant, ink present). Writes a report + thumbnails of any
candidate text page. Read-only."""
import struct, sys, os, json, glob
sys.path.insert(0, "C:/programmieren/wizardrytranslation/tools")
from psmt4_deswizzle import deswizzle_psmt4
from collections import Counter
from PIL import Image

RAW = "C:/programmieren/wizardrytranslation/extracted/packdata_raw"
OUT = "C:/programmieren/wizardrytranslation/build/recon_cine/cinematics"
_LOG = []
def log(*a):
    _LOG.append(" ".join(str(x) for x in a))


def parse_sections(d):
    secs = []; i = 0
    while (i + 1) * 16 <= len(d):
        sid, size, off, flags = struct.unpack_from("<4I", d, i * 16)
        if sid != i or off >= len(d) or size == 0 or size > len(d):
            break
        secs.append((sid, size, off, flags)); i += 1
        if secs[0][2] <= i * 16:
            break
    return secs


def sub_images(d, off, size):
    """Return list of (psm, tw, th, upw, src, nbytes) for big uploads."""
    s = d[off:off + size]
    if len(s) < 16:
        return []
    A, B = struct.unpack_from("<2I", s, 0)
    if not (0 < A < 64 and 0 < B < 64):
        return []
    tex_dims = []
    for p in range(A):
        base = 16 + p * 0x50
        if base + 0x50 > len(s):
            return []
        lo, hi = struct.unpack_from("<QQ", s, base + 16 + 3 * 16)
        if (hi & 0xFF) in (0x06, 0x07):
            psm = (lo >> 20) & 0x3F
            tw = 1 << ((lo >> 26) & 0xF)
            th = 1 << ((lo >> 30) & 0xF)
            tex_dims.append((tw, th, psm))
    cells_off = 16 + A * 0x50
    up_off = cells_off + A * 20
    ups = []
    for b in range(B):
        if up_off + b * 16 + 16 > len(s):
            return []
        pad, f0, w, h, cnt = struct.unpack_from("<IIHHI", s, up_off + b * 16)
        ups.append({"w": w, "h": h, "bytes": w * h * 4})
    total = sum(u["bytes"] for u in ups)
    payload = (up_off + B * 16 + 15) & ~15
    if 0 < total <= size and size - total >= up_off + B * 16:
        payload = size - total
    if not tex_dims:
        tex_dims = [(256, 256, 0x14)]
    tw, th, psm = sorted(set(tex_dims), key=lambda t: -(t[0] * t[1]))[0]
    out = []
    src = payload
    for u in ups:
        if u["bytes"] > 4096 and psm == 0x14:
            out.append((psm, tw, th, u["w"], off + src, u["bytes"]))
        src += u["bytes"]
    return out


def analyze(d, psm, tw, th, upw, src, nbytes, tag):
    data = d[src:src + nbytes]
    etw, eth = tw, th
    if nbytes * 2 != tw * th:
        eth = max(16, nbytes * 2 // tw)
    try:
        px = deswizzle_psmt4(data, etw, eth, bw_psmt4=etw, dbw_ct32=upw)
    except Exception:
        return None
    c = Counter(px)
    bg, bgn = c.most_common(1)[0]
    n = len(px)
    bg_frac = bgn / n
    ink = sum(v for k, v in c.items() if k != bg)
    # text page heuristic: bg index 15 (inverted ramp), bg dominant 50-98%,
    # ink spread across many rows
    if bg != 15:
        return None
    if not (0.45 < bg_frac < 0.985):
        return None
    rows_with_ink = len({i // etw for i, v in enumerate(px) if v != bg})
    if rows_with_ink < 20:
        return None
    # save thumbnail
    im = Image.frombytes("L", (etw, eth),
                         bytes(min(255, v * 17) for v in px))
    name = f"scan_{tag}_{etw}x{eth}_dbw{upw}_off{src}.png"
    im.save(os.path.join(OUT, name))
    return {"tag": tag, "off": src, "tex": f"{etw}x{eth}", "dbw": upw,
            "bg_frac": round(bg_frac, 3), "rows_ink": rows_with_ink,
            "png": name}


def main():
    files = []
    for t in ("07", "09", "11", "15"):
        files += sorted(glob.glob(f"{RAW}/*_type{t}.raw"))
    found = []
    for fp in files:
        rid = int(os.path.basename(fp)[:4])
        d = open(fp, "rb").read()
        secs = parse_sections(d)
        for sid, size, off, flags in secs:
            for img in sub_images(d, off, size):
                r = analyze(d, *img, f"r{rid}s{sid}")
                if r:
                    r["resource"] = rid; r["sub"] = sid
                    found.append(r)
                    log(f"TEXT? r{rid}s{sid} {r['tex']} dbw{r['dbw']} "
                        f"off{r['off']} bgfrac{r['bg_frac']} "
                        f"rows{r['rows_ink']} -> {r['png']}")
    json.dump(found, open(os.path.join(OUT, "scan_all.json"), "w"), indent=1)
    log(f"\nTotal candidate text pages: {len(found)}")


main()
open(os.path.join(OUT, "scan_all_log.txt"), "w", encoding="utf-8").write(
    "\n".join(_LOG))
