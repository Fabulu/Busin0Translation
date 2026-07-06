#!/usr/bin/env python3
"""qa_corpus_dryrun.py -- no-build corpus QA for the wrap/centering waves.

Replays the ENTIRE translated corpus through the SHIPPING wrap helpers and
reports, per group: line count under the current char-count wrap vs the raw
(unwrapped) line count, plus every line whose glyph_metrics.px_width exceeds the
dialogue-frame budget.  Reads ONLY data/ + tools/ -- writes NO ISO, runs in
seconds, deterministic (re-run => byte-identical stdout).  This is the per-wave
gate for P2 (pixel wrap) / P3 (centering): run it, diff the table.

Corpus:
  * data/type2_translated/batch_*.json   (type-2 dialogue/narration; build_v9
    load filters mirrored: SKIP_STRUCTURAL_GROUPS {(1197,1)}, empty,
    [DATA]/[LAYOUT]/[BINARY]/[MAP]/[SYSTEM]/[GLYPH/[DEBUG] prefixes, any ord>127)
  * data/translate_chunks/chunk_00..09 + fix files  (type-01 word_wrap=18)
  * tools/patch_r1193_narration.TRAILING_PAGES        (R1193 trailing, <=23)

The build_v9 wrap helpers (_wrap_line/wrap_type2_text/reflow_dialogue) are
EXEC-ISOLATED from build_v9 source -- build_v9.py runs a full ISO build at import
(os.chdir + os.system, no __main__ guard) so it cannot be imported.
"""
import glob
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import glyph_metrics                                   # noqa: E402
from dialogue_classifier import build_dialogue_map      # noqa: E402
import patch_r1193_narration as r1193                   # noqa: E402


# ---- pull the 3 wrap helpers out of build_v9 WITHOUT running the build -------
def _load_wrap_helpers():
    src = open(os.path.join(ROOT, "build", "build_v9.py"), encoding="utf-8").read()
    m = re.search(r"^TYPE2_WRAP_WIDTH\s*=\s*(\d+)", src, re.M)
    assert m, "TYPE2_WRAP_WIDTH not found in build_v9.py"
    width = int(m.group(1))
    mb = re.search(r"^DIALOGUE_BOX_PX\s*=\s*(\d+)", src, re.M)
    assert mb, "DIALOGUE_BOX_PX not found in build_v9.py"
    box_px = int(mb.group(1))
    # extract each pure def by name (they reference only each other + width +
    # the module-level glyph_metrics which wrap_px/_wrap_line_px need at runtime)
    ns = {"TYPE2_WRAP_WIDTH": width, "DIALOGUE_BOX_PX": box_px,
          "glyph_metrics": glyph_metrics, "enc": _enc}
    for fn in ("_wrap_line", "wrap_type2_text", "reflow_dialogue",
               "_wrap_line_px", "wrap_px"):
        mm = re.search(r"^def %s\(.*?(?=^\S|\Z)" % fn, src, re.M | re.S)
        assert mm, "def %s not found in build_v9.py" % fn
        exec(compile(mm.group(0), "build_v9:%s" % fn, "exec"), ns)
    return (width, box_px, ns["_wrap_line"], ns["wrap_type2_text"],
            ns["reflow_dialogue"], ns["_wrap_line_px"], ns["wrap_px"])

# enc family identical to build_v9 / patch_r1193 (char-32; English fallback 31)
_TBL = json.load(open(os.path.join(ROOT, "data", "english_glyph_table.json"),
                     encoding="utf-8"))


def _enc(ch):
    if ch in _TBL:
        return int(_TBL[ch])
    if ch.lower() in _TBL:
        return int(_TBL[ch.lower()])
    return 0 if ch == " " else 31


# Loaded AFTER _enc: wrap_px / _wrap_line_px capture _enc into their exec
# namespace for glyph_metrics.px_width(seg, enc).
(WIDTH, BOX_PX, _wrap_line, wrap_type2_text, reflow_dialogue,
 _wrap_line_px, wrap_px) = _load_wrap_helpers()

PX_BUDGET = 23 * 18  # 23 cells * the v98 18px dialogue advance ceiling, as a
                     # coarse frame-width bound for the px offender report


def _lines(text):
    out = []
    for page in text.split(" // "):
        out.extend(page.split(" / "))
    return out


SKIP_STRUCTURAL = {(1197, 1)}
SKIP_PREFIXES = ("[DATA]", "[LAYOUT]", "[BINARY]", "[MAP]",
                 "[SYSTEM]", "[GLYPH", "[DEBUG]")


def _wanted_type2(res, mi, en):
    if res is None or mi is None:
        return False
    if (res, mi) in SKIP_STRUCTURAL:
        return False
    if not en:
        return False
    if any(en.startswith(p) for p in SKIP_PREFIXES):
        return False
    if any(ord(c) > 127 for c in en):
        return False
    return True


# build_dialogue_map walks Section 1 per resource -- memoize per distinct res.
_DMAP_CACHE = {}


def _dmap(res):
    if res not in _DMAP_CACHE:
        _DMAP_CACHE[res] = build_dialogue_map(res)
    return _DMAP_CACHE[res]


def main():
    rows = []   # (res, mi, kind, raw_lines, new_lines, max_px, n_overflow)
    # ---- type-2 ----
    for fn in sorted(glob.glob(os.path.join(ROOT, "data", "type2_translated",
                                            "batch_*.json"))):
        for e in json.load(open(fn, encoding="utf-8")):
            res, mi, en = e.get("resource"), e.get("msg_index"), e.get("english", "")
            if not _wanted_type2(res, mi, en):
                continue
            dmap = _dmap(res)
            txt = en
            # Dialogue path: T4 324px px-wrap (matches build_v9's Step-4 branch).
            # Non-dialogue: byte-identical char-20 wrap_type2_text as before.
            if mi in dmap:
                new = wrap_px(txt, BOX_PX)
            else:
                new = wrap_type2_text(txt)
            raw_n = len(_lines(en))
            new_lines = _lines(new)
            pxs = [glyph_metrics.px_width(ln, _enc) for ln in new_lines]
            rows.append((res, mi, "dlg" if mi in dmap else "txt",
                         raw_n, len(new_lines),
                         max(pxs) if pxs else 0,
                         sum(1 for p in pxs if p > PX_BUDGET)))
    # ---- type-01 chunks (word_wrap=18, a DIFFERENT default) ----
    chunk_files = [os.path.join(ROOT, "data", "translate_chunks",
                                "chunk_%02d_translated.json" % i) for i in range(10)]
    for fn in chunk_files:
        if not os.path.isfile(fn):
            continue
        for e in json.load(open(fn, encoding="utf-8")):
            res, mi = e.get("resource", -1), e.get("message", -1)
            if res is None or mi is None:
                continue
            en = (e.get("english", "") or "").strip()
            if not en or en == e.get("japanese", ""):
                continue
            if any(ord(c) > 127 for c in en):
                continue
            # type-01 uses word_wrap(max_chars=18); reuse _wrap_line at 18 to
            # mirror its per-segment wrap (preserves authored ' / ')
            wrapped = " / ".join(
                seg for s in en.split(" / ") for seg in _wrap_line(s, 18))
            new_lines = _lines(wrapped)
            pxs = [glyph_metrics.px_width(ln, _enc) for ln in new_lines]
            rows.append((res, mi, "t01", len(_lines(en)), len(new_lines),
                         max(pxs) if pxs else 0,
                         sum(1 for p in pxs if p > PX_BUDGET)))
    # ---- R1193 trailing narration (fixed 23-record budget) ----
    for pi, page in enumerate(r1193.TRAILING_PAGES):
        n = r1193.PAGE_LINES[pi]
        page_lines = r1193._flow_page(page, n)
        pxs = [glyph_metrics.px_width(ln, _enc) for ln in page_lines]
        rows.append((1193, 990 + pi, "nar", n, len(page_lines),
                     max(pxs) if pxs else 0,
                     sum(1 for p in pxs if p > r1193.MAX_LINE_GLYPHS * 18)))

    rows.sort(key=lambda r: (r[0], r[1]))
    print("# qa_corpus_dryrun  width=%d  box_px=%d  px_budget=%d  rows=%d"
          % (WIDTH, BOX_PX, PX_BUDGET, len(rows)))
    print("# %-5s %-6s %-4s %4s %4s %6s %4s"
          % ("res", "mi", "kind", "rawL", "newL", "maxpx", "ovf"))
    n_grow = n_ovf = 0
    dlg_4plus = 0       # dialogue-classified groups wrapping to >=4 lines (T4 metric)
    dlg_px_over = 0     # dialogue rows whose widest line exceeds the 324px ceiling
    for res, mi, kind, rawn, newn, mpx, ovf in rows:
        if newn > rawn:
            n_grow += 1
        if ovf:
            n_ovf += 1
        if kind == "dlg":
            if newn >= 4:
                dlg_4plus += 1
            if mpx > BOX_PX:
                dlg_px_over += 1
        print("R%-5d %-6s %-4s %4d %4d %6d %4d"
              % (res, mi, kind, rawn, newn, mpx, ovf))
    print("# SUMMARY rows=%d grew_lines=%d px_overflow_rows=%d"
          % (len(rows), n_grow, n_ovf))
    print("# T4 dialogue: dlg_groups_4plus_lines=%d  dlg_rows_over_%dpx=%d"
          % (dlg_4plus, BOX_PX, dlg_px_over))
    return 0


if __name__ == "__main__":
    sys.exit(main())
