#!/usr/bin/env python3
"""
regress_diff.py -- emulator-free differential regression gates for a candidate
PS2 build, driven off PCSX2 save-states (.p2s) via tools/p2s_extract.py.

The two v171 regressions this harness is built to AUTO-CATCH once golden
baselines exist:

  * post-chargen BLACK SCREEN  -> png_tripwire (a Screenshot.png byte-size
    tripwire; no image decode needed).  black frame ~2909 B vs 200-460 KB good.
  * garbled chargen text        -> pixel_diff over a text-rect MASK vs a golden
    frame (a mask over the stat sidebar / name row lights up on garble/overflow).

Plus two guardrails that make any diff trustworthy:

  * build_match  -- abort if a save-state's embedded EE RAM does not match the
    candidate EXE at known patch VAs (a STALE save silently "passes" otherwise;
    save-states embed the OLD EXE image).  ee is VA-direct; the EXE FILE uses
    fo(va) = va - 0x100000 + 0x80.
  * ram_manifest_diff -- diff the EXE/.text EE window between two dumps; any
    differing VA NOT covered by the intended patch manifest = a regression
    (the runtime twin of the static patch allowlist; also detects the
    DMA-swept-table class where a table VA mutates mid-battle).

Each gate is a plain function returning a small result dict with a boolean
"ok" plus an explanation, AND a CLI subcommand.  Nothing here imports the
build; it only reads .p2s + EXE bytes, so it is safe to run any time.

Pillow is required ONLY for pixel_diff (image decode).  Every other gate works
without it.
"""

import argparse
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2s_extract

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

# -- EXE address math ------------------------------------------------------
# EE RAM image is VA-direct.  The EXE FILE on disc maps a VA to a file offset:
EXE_LOAD_VA = 0x100000
EXE_FILE_BASE = 0x80


def exe_fo(va):
    """File offset of a virtual address inside the SLPM_653.78 EXE image."""
    return va - EXE_LOAD_VA + EXE_FILE_BASE


# Default probe VAs for build_match: known patch/hook sites whose word differs
# between pristine and a patched build.  0x3A31A0 is the Patch-27 hook site
# (a relocated cave j-word in a patched EXE); 0x309820... etc could be added.
# Callers may override.  These are READ from both the ee dump and the candidate
# EXE and required equal (proving the save was captured from that EXE build).
DEFAULT_PROBE_VAS = (0x3A31A0,)

# Screenshot.png byte-size floor below which a frame is treated as black/blank.
DEFAULT_PNG_FLOOR = 10000


# ===========================================================================
# GATE 1 -- PNG size tripwire (near-free; no image decode)
# ===========================================================================
def png_tripwire(candidate_p2s, baseline_p2s=None, abs_floor=DEFAULT_PNG_FLOOR,
                 rel_frac=0.25):
    """FAIL if the candidate Screenshot.png is byte-suspiciously small.

    Two independent triggers:
      * absolute: candidate size < abs_floor  (catches the ~2909 B black frame)
      * relative: baseline given AND candidate < rel_frac * baseline size
                  (catches a frame that collapsed vs a known-good golden)

    Returns {ok, cand_bytes, base_bytes, reason}.  No PNG is decoded.
    """
    cand = len(p2s_extract.screenshot(candidate_p2s))
    base = None
    reasons = []
    ok = True
    if cand < abs_floor:
        ok = False
        reasons.append("candidate frame %d B < absolute floor %d B (BLACK/blank)"
                       % (cand, abs_floor))
    if baseline_p2s is not None:
        base = len(p2s_extract.screenshot(baseline_p2s))
        if cand < rel_frac * base:
            ok = False
            reasons.append("candidate frame %d B < %.0f%% of baseline %d B"
                           % (cand, rel_frac * 100, base))
    if ok:
        reasons.append("frame %d B >= floor%s -- OK"
                       % (cand, "" if base is None else " and >=%.0f%% of %d B baseline"
                          % (rel_frac * 100, base)))
    return {"ok": ok, "cand_bytes": cand, "base_bytes": base,
            "reason": "; ".join(reasons)}


# ===========================================================================
# GATE 2 -- build-match (abort on a stale save)
# ===========================================================================
def build_match(p2s, candidate_exe, probe_vas=DEFAULT_PROBE_VAS):
    """Assert the save-state's EE RAM matches candidate_exe at probe VAs.

    ee is VA-direct; the EXE file uses exe_fo(va).  Any mismatch => the save
    was captured from a DIFFERENT EXE build (STALE) => the harness must ABORT
    rather than trust the diff.

    Returns {ok, mismatches:[(va, ram_word, exe_word)], reason}.
    """
    ee = p2s_extract.ee_ram(p2s)
    if isinstance(candidate_exe, (bytes, bytearray)):
        exe = candidate_exe
    else:
        exe = open(candidate_exe, "rb").read()
    mism = []
    for va in probe_vas:
        ram_w = struct.unpack_from("<I", ee, va)[0]
        fo = exe_fo(va)
        if fo + 4 > len(exe):
            mism.append((va, ram_w, None))
            continue
        exe_w = struct.unpack_from("<I", exe, fo)[0]
        if ram_w != exe_w:
            mism.append((va, ram_w, exe_w))
    ok = not mism
    if ok:
        reason = ("save matches candidate EXE at %d probe VA(s): %s -- FRESH"
                  % (len(probe_vas), ", ".join("0x%X" % v for v in probe_vas)))
    else:
        reason = ("STALE save -- %d probe mismatch(es): "
                  % len(mism)) + "; ".join(
            "VA 0x%X ram=0x%08X exe=%s"
            % (va, rw, "OOB" if ew is None else "0x%08X" % ew)
            for va, rw, ew in mism)
    return {"ok": ok, "mismatches": mism, "reason": reason}


# ===========================================================================
# GATE 3 -- masked framebuffer pixel diff (Pillow)
# ===========================================================================
def _load_png(src):
    """Return (Image RGBA, w, h). src may be a path or raw PNG bytes."""
    try:
        from PIL import Image
    except ImportError as e:
        raise RuntimeError(
            "pixel_diff needs Pillow (pip install Pillow) -- %s" % e)
    import io
    if isinstance(src, (bytes, bytearray)):
        im = Image.open(io.BytesIO(src))
    else:
        im = Image.open(src)
    im = im.convert("RGBA")
    return im, im.width, im.height


def pixel_diff(baseline_png, candidate_png, masks=None, chan_thresh=8,
               heatmap_out=None):
    """Compare two frames; report %pixels changed + changed bbox + per-mask %.

    A pixel counts as CHANGED if ANY channel delta > chan_thresh.
    baseline_png / candidate_png may be file paths OR raw PNG bytes.
    masks: optional list of (name, x0, y0, x1, y1) rects -> per-mask %changed
           (a mask over a text rect catches garble / overflow locally).
    heatmap_out: optional path -> write a red-on-black changed-pixel heatmap.

    Returns {ok(bool placeholder=True), pct_changed, n_changed, n_total,
             bbox, size, masks:{name:pct}, heatmap}.  Callers decide the
    pass/fail threshold per scene; this function just measures.
    """
    base_im, bw, bh = _load_png(baseline_png)
    cand_im, cw, ch = _load_png(candidate_png)
    if (bw, bh) != (cw, ch):
        return {"ok": False, "pct_changed": 100.0, "n_changed": None,
                "n_total": None, "bbox": None, "size": (cw, ch),
                "masks": {}, "heatmap": None,
                "reason": "frame size mismatch base=%dx%d cand=%dx%d"
                          % (bw, bh, cw, ch)}
    bpx = base_im.load()
    cpx = cand_im.load()
    n_total = bw * bh
    n_changed = 0
    min_x, min_y, max_x, max_y = bw, bh, -1, -1
    changed = bytearray(n_total)  # 1 per changed pixel, row-major
    for y in range(bh):
        row = y * bw
        for x in range(bw):
            b = bpx[x, y]
            c = cpx[x, y]
            if (abs(b[0] - c[0]) > chan_thresh or abs(b[1] - c[1]) > chan_thresh
                    or abs(b[2] - c[2]) > chan_thresh or abs(b[3] - c[3]) > chan_thresh):
                n_changed += 1
                changed[row + x] = 1
                if x < min_x:
                    min_x = x
                if x > max_x:
                    max_x = x
                if y < min_y:
                    min_y = y
                if y > max_y:
                    max_y = y
    pct = 100.0 * n_changed / n_total if n_total else 0.0
    bbox = None if max_x < 0 else (min_x, min_y, max_x, max_y)

    mask_pcts = {}
    if masks:
        for name, x0, y0, x1, y1 in masks:
            x0c, x1c = max(0, x0), min(bw, x1)
            y0c, y1c = max(0, y0), min(bh, y1)
            tot = max(0, (x1c - x0c)) * max(0, (y1c - y0c))
            if tot == 0:
                mask_pcts[name] = 0.0
                continue
            cnt = 0
            for y in range(y0c, y1c):
                row = y * bw
                for x in range(x0c, x1c):
                    if changed[row + x]:
                        cnt += 1
            mask_pcts[name] = 100.0 * cnt / tot

    heat_path = None
    if heatmap_out:
        from PIL import Image
        heat = Image.new("RGB", (bw, bh), (0, 0, 0))
        hpx = heat.load()
        for y in range(bh):
            row = y * bw
            for x in range(bw):
                if changed[row + x]:
                    hpx[x, y] = (255, 40, 40)
        heat.save(heatmap_out)
        heat_path = heatmap_out

    return {"ok": True, "pct_changed": pct, "n_changed": n_changed,
            "n_total": n_total, "bbox": bbox, "size": (bw, bh),
            "masks": mask_pcts, "heatmap": heat_path,
            "reason": "%.3f%% pixels changed (%d/%d), bbox=%s"
                      % (pct, n_changed, n_total, bbox)}


# ===========================================================================
# GATE 4 -- RAM manifest diff (EXE/.text window vs an intended-patch allowlist)
# ===========================================================================
def _covered(va, allow):
    for a_va, a_len in allow:
        if a_va <= va < a_va + a_len:
            return True
    return False


def ram_manifest_diff(baseline_p2s, candidate_p2s, exe_lo=0x100000,
                      exe_hi=0x4B0000, allow_vas=None, max_report=40):
    """Diff the EE EXE/.text window between two dumps; flag un-allowed deltas.

    Any VA in [exe_lo, exe_hi) whose byte differs between baseline and
    candidate AND is NOT covered by allow_vas (the intended patch manifest,
    a list of (va, len)) is a REGRESSION.

    allow_vas: list of (va, byte_len) spans the build is ALLOWED to change.
               (Parsing patch_exe.py to derive this automatically is a TODO;
               for v1 the caller passes the manifest explicitly.)

    Returns {ok, n_diff, n_unallowed, first_unallowed, runs, reason}.
    `runs` groups the un-allowed diffs into contiguous (va, length) spans.
    """
    allow = list(allow_vas or [])
    base = p2s_extract.ee_ram(baseline_p2s)
    cand = p2s_extract.ee_ram(candidate_p2s)
    hi = min(exe_hi, len(base), len(cand))
    n_diff = 0
    unallowed = []
    va = exe_lo
    while va < hi:
        if base[va] != cand[va]:
            n_diff += 1
            if not _covered(va, allow):
                unallowed.append(va)
        va += 1
    # group un-allowed diffs into contiguous runs
    runs = []
    for v in unallowed:
        if runs and v == runs[-1][0] + runs[-1][1]:
            runs[-1] = (runs[-1][0], runs[-1][1] + 1)
        else:
            runs.append((v, 1))
    ok = not unallowed
    if ok:
        reason = ("%d byte diffs in [0x%X,0x%X), all covered by the %d-span "
                  "manifest -- OK" % (n_diff, exe_lo, hi, len(allow)))
    else:
        reason = ("REGRESSION: %d/%d diffs OUTSIDE the patch manifest, in %d "
                  "run(s); first at VA 0x%X"
                  % (len(unallowed), n_diff, len(runs), unallowed[0]))
    return {"ok": ok, "n_diff": n_diff, "n_unallowed": len(unallowed),
            "first_unallowed": unallowed[0] if unallowed else None,
            "runs": runs[:max_report], "reason": reason}


# ===========================================================================
# CLI
# ===========================================================================
def _parse_masks(spec):
    """'name:x0,y0,x1,y1;name2:...' -> [(name,x0,y0,x1,y1)]."""
    out = []
    if not spec:
        return out
    for part in spec.split(";"):
        part = part.strip()
        if not part:
            continue
        name, rect = part.split(":")
        x0, y0, x1, y1 = (int(v) for v in rect.split(","))
        out.append((name.strip(), x0, y0, x1, y1))
    return out


def _parse_allow(spec):
    """'va:len,va:len' (hex or dec) -> [(va,len)]."""
    out = []
    if not spec:
        return out
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        va, ln = part.split(":")
        out.append((int(va, 0), int(ln, 0)))
    return out


def _main(argv=None):
    ap = argparse.ArgumentParser(description="Differential regression gates for a PS2 build.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("png", help="PNG-size tripwire (black-screen class)")
    p.add_argument("candidate")
    p.add_argument("--baseline")
    p.add_argument("--floor", type=int, default=DEFAULT_PNG_FLOOR)

    p = sub.add_parser("build-match", help="abort on a stale save (probe VAs)")
    p.add_argument("p2s")
    p.add_argument("exe")
    p.add_argument("--probe", help="comma VAs (hex ok), default 0x3A31A0")

    p = sub.add_parser("pixel", help="masked framebuffer pixel-diff (needs Pillow)")
    p.add_argument("baseline", help="baseline PNG or .p2s")
    p.add_argument("candidate", help="candidate PNG or .p2s")
    p.add_argument("--masks", help="name:x0,y0,x1,y1;...")
    p.add_argument("--thresh", type=int, default=8)
    p.add_argument("--heatmap")

    p = sub.add_parser("ram", help="EXE-window RAM diff vs a patch allowlist")
    p.add_argument("baseline")
    p.add_argument("candidate")
    p.add_argument("--lo", default="0x100000")
    p.add_argument("--hi", default="0x4B0000")
    p.add_argument("--allow", help="va:len,va:len (intended-patch manifest)")

    args = ap.parse_args(argv)

    def _pngsrc(path):
        """Accept a .p2s (extract its Screenshot.png) or a raw PNG file."""
        if path.lower().endswith(".p2s"):
            return p2s_extract.screenshot(path)
        return path

    if args.cmd == "png":
        r = png_tripwire(args.candidate, args.baseline, abs_floor=args.floor)
    elif args.cmd == "build-match":
        probes = ([int(v, 0) for v in args.probe.split(",")] if args.probe
                  else DEFAULT_PROBE_VAS)
        r = build_match(args.p2s, args.exe, probes)
    elif args.cmd == "pixel":
        r = pixel_diff(_pngsrc(args.baseline), _pngsrc(args.candidate),
                       masks=_parse_masks(args.masks), chan_thresh=args.thresh,
                       heatmap_out=args.heatmap)
    elif args.cmd == "ram":
        r = ram_manifest_diff(args.baseline, args.candidate,
                              exe_lo=int(args.lo, 0), exe_hi=int(args.hi, 0),
                              allow_vas=_parse_allow(args.allow))
    else:  # pragma: no cover
        ap.error("unknown cmd")

    status = "PASS" if r.get("ok") else "FAIL"
    print("[%s] %s" % (status, r.get("reason", "")))
    for k, v in r.items():
        if k in ("ok", "reason"):
            continue
        print("    %-14s %s" % (k, v))
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    sys.exit(_main())
