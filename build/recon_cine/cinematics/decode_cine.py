#!/usr/bin/env python3
"""Decode all sheet subs across cinematic-family resources R2879-R2882 to
find baked text pages. Read-only; writes gray PNGs under this dir."""
import struct, sys, os, json
sys.path.insert(0, "C:/programmieren/wizardrytranslation/tools")
from psmt4_deswizzle import deswizzle_psmt4
from psmt8_deswizzle import deswizzle_psmt8
from PIL import Image

RAW = "C:/programmieren/wizardrytranslation/extracted/packdata_raw"
OUT = "C:/programmieren/wizardrytranslation/build/recon_cine/cinematics"

_LOG = []
def print(*a, **k):  # noqa: A001
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


def decode_sheet_sub(d, off, size, tag):
    s = d[off:off + size]
    if len(s) < 16:
        return None
    A, B = struct.unpack_from("<2I", s, 0)
    if not (0 < A < 64 and 0 < B < 64):
        return None
    tex_dims = []
    for p in range(A):
        base = 16 + p * 0x50
        if base + 0x50 > len(s):
            return None
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
            return None
        pad, f0, w, h, cnt = struct.unpack_from("<IIHHI", s, up_off + b * 16)
        ups.append({"f0": f0, "w": w, "h": h, "cnt": cnt, "bytes": w * h * 4})
    payload = (up_off + B * 16 + 15) & ~15
    total = sum(u["bytes"] for u in ups)
    if 0 < total <= size and size - total >= up_off + B * 16:
        payload = size - total
    if not tex_dims:
        tex_dims = [(256, 256, 0x14)]
    tw, th, psm = sorted(set(tex_dims), key=lambda t: -(t[0] * t[1]))[0]
    bigimgs = [(u['w'], u['h']) for u in ups if u['bytes'] > 1024]
    print(f"  {tag}: A={A} B={B} payload=file+{off+payload} tex={tw}x{th} "
          f"psm=0x{psm:X} imgs={bigimgs}")
    src = payload
    images, cluts = [], []
    for u in ups:
        u["src"] = src
        if u["bytes"] > 1024:
            images.append(u)
        else:
            cluts.append(s[src:src + 64])
        src += u["bytes"]
    pngs = []
    for ui, u in enumerate(images):
        data = s[u["src"]:u["src"] + u["bytes"]]
        etw, eth = tw, th
        if psm == 0x14:
            if u["bytes"] * 2 != tw * th:
                eth = max(16, u["bytes"] * 2 // tw)
            px = deswizzle_psmt4(data, etw, eth, bw_psmt4=etw, dbw_ct32=u["w"])
            scale = 17
        elif psm == 0x13:
            if u["bytes"] != tw * th:
                eth = max(16, u["bytes"] // tw)
            px = deswizzle_psmt8(data, etw, eth, bw_psmt8=etw, dbw_ct32=u["w"])
            scale = 1
        else:
            continue
        im = Image.frombytes("L", (etw, eth),
                             bytes(min(255, v * scale) for v in px))
        name = f"{tag}_img{ui}_{etw}x{eth}_p{psm:02X}_off{off+u['src']}.png"
        im.save(os.path.join(OUT, name))
        pngs.append(name)
    return {"tag": tag, "off": off, "size": size, "tex": [tw, th, psm],
            "n_images": len(images), "pngs": pngs,
            "img_offsets": [off + u["src"] for u in images]}


def main():
    targets = [(2879, 7), (2880, 11), (2881, 15), (2882, 9)]
    rep = []
    for rid, t in targets:
        fp = f"{RAW}/{rid:04d}_type{t:02d}.raw"
        d = open(fp, "rb").read()
        secs = parse_sections(d)
        print(f"=== R{rid}: {len(d)}B, {len(secs)} sections")
        for sid, size, off, flags in secs:
            try:
                r = decode_sheet_sub(d, off, size, f"r{rid}s{sid}")
            except Exception as e:
                print(f"  r{rid}s{sid}: ERR {e}")
                r = None
            if r:
                r["resource"] = rid; r["sub"] = sid
                rep.append(r)
    json.dump(rep, open(os.path.join(OUT, "decode_cine.json"), "w"), indent=1)
    print("wrote decode_cine.json,", len(rep), "sheets")


main()
open(os.path.join(OUT, "decode_log.txt"), "w", encoding="utf-8").write(
    "\n".join(_LOG))
