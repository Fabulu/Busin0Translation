#!/usr/bin/env python3
"""
token_audit.py -- control-token preservation audit for type-02 dialogue groups
(RUN-20261011-2104, v203 token-preservation pass).

The Step-4 injector keeps only a group's LEADING and TRAILING control runs
(_split_control_and_text); every control word BETWEEN the first and last JP
text glyph was silently dropped unless the English authored it inline as a
"[FXXX]" token.  That lost character-name inserts, lottery numbers, overheard-
chat page waits, the fortune teller's result, shake effects, and left glow /
highlight runs open for the rest of a message.

audit_group(pristine, built, allowed_missing) compares one FFFF-group:

  ERRORS (must be zero for a translated group)
    * FUNCTIONAL multiset mismatch -- every word in FUNCTIONAL (inserts,
      page waits, effect/timing/position controls) must survive with the same
      count, except the deliberately stripped leading variable insert
      (allowed_missing, see _strip_leading_var_insert).
    * END-STATE mismatch -- the glow flag (FB01/FB00), highlight index
      (FFE0-FFE7), colour (FFD0-FFD9) and shake mode (FB02-FB05) in force
      after the group's last word must equal pristine's, so no run is left
      open (or closed) differently than the JP author wrote it.
  WARNINGS (fidelity, not correctness)
    * fewer glow/highlight openers than pristine (an emphasized item name
      lost its emphasis).

CLI (authoring check):
    python -X utf8 tools/token_audit.py <proposals.json>
  proposals.json = [{"resource": R, "msg_index": G, "english": "..."}]
  Runs the REAL injector (inject_and_patch) on the proposals and audits every
  proposed group against pristine.  Exit 1 on any error.
"""

import collections
import os
import re
import struct
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)

# Inserts (FE00 registered string, FE01..FE0F numbers, FFF0..FFF6 names),
# FFFD page wait, FB02..FB05 shake modes, FC00..FC0A x-position,
# FD00..FD27 typewriter delay.  FB06..FB09 are engine no-ops (EXE 0x3097E0)
# and FFFE line breaks are re-authored by the wrapper -- neither is judged.
FUNCTIONAL = (set(range(0xFE00, 0xFE10)) | set(range(0xFFF0, 0xFFF7)) | {0xFFFD}
              | set(range(0xFB02, 0xFB06)) | set(range(0xFC00, 0xFC0B))
              | set(range(0xFD00, 0xFD28)))
VAR_INSERTS = set(range(0xFFF0, 0xFFF7))
CTRL_TOKEN_RE = re.compile(r'(\[F[BCDEF][0-9A-F]{2}\])')


def end_state(group):
    """(glow, highlight, colour, shake) in force after the group's last word.
    Every one of these is reset per message by the draw routine (EXE
    0x3080C4..0x308114), so the state at the FFFF is what a later word in the
    same message would inherit."""
    glow = hl = col = shake = None
    for w in group:
        if w in (0xFB00, 0xFB01):
            glow = w
        elif 0xFFE0 <= w <= 0xFFE7:
            hl = w
        elif 0xFFD0 <= w <= 0xFFD9:
            col = w
        elif 0xFB02 <= w <= 0xFB05:
            shake = w
    # FB00 / FFE0 / FB02 are the engine defaults: "never set" == "reset".
    return (glow if glow != 0xFB00 else None,
            hl if hl != 0xFFE0 else None,
            col, shake if shake != 0xFB02 else None)


def audit_group(pristine, built, allowed_missing=()):
    """Return (errors, warnings) lists of strings for one group."""
    errs, warns = [], []
    fp = collections.Counter(w for w in pristine if w in FUNCTIONAL)
    fb = collections.Counter(w for w in built if w in FUNCTIONAL)
    allow = collections.Counter(allowed_missing)
    missing = fp - fb
    extra = fb - fp
    missing = missing - allow
    if missing:
        errs.append("lost " + " ".join("%04X x%d" % (k, v) for k, v in sorted(missing.items())))
    if extra:
        errs.append("extra " + " ".join("%04X x%d" % (k, v) for k, v in sorted(extra.items())))
    sp, sb = end_state(pristine), end_state(built)
    names = ("glow FB01", "highlight FFE*", "colour FFD*", "shake FB0x")
    for n, a, b in zip(names, sp, sb):
        if a != b:
            errs.append("end-state %s: pristine %s, built %s" % (
                n, "%04X" % a if a else "reset", "%04X" % b if b else "reset"))
    for lab, opener in (("glow", lambda w: w == 0xFB01),
                        ("highlight", lambda w: 0xFFE1 <= w <= 0xFFE7)):
        cp = sum(1 for w in pristine if opener(w))
        cb = sum(1 for w in built if opener(w))
        if cb < cp:
            warns.append("%s openers %d < pristine %d" % (lab, cb, cp))
    return errs, warns


# ---------------------------------------------------------------------------
# Resource-level helpers (shared with tests/test_token_preservation.py)
# ---------------------------------------------------------------------------
def groups_of(data):
    """FFFF-delimited Section-2 groups of a type-02 blob."""
    off = struct.unpack_from("<I", data, 0x18)[0]
    size = struct.unpack_from("<I", data, 0x14)[0]
    words = struct.unpack_from(">%dH" % (size // 2), data, off)
    out, cur = [], []
    for w in words:
        if w == 0xFFFF:
            out.append(cur)
            cur = []
        else:
            cur.append(w)
    return out


def stripped_leading_vars(pristine_data):
    """{group_index: [var-insert words]} that the injector DELIBERATELY drops:
    the head run of FFF0..FFF6 in a group's leading control run (after any
    clean 0x14 label prefix) -- see _strip_leading_var_insert."""
    from sec1_disasm import walk, extract_records
    from patch_section1_offsets import (_bucket_labels, _clean_prefix_len,
                                        _split_control_and_text)
    so = struct.unpack_from("<I", pristine_data, 0x18)[0]
    sec1 = bytes(pristine_data[0x20:so])
    groups = groups_of(pristine_data)
    ranges, pos = [], 0
    for g in groups:
        ranges.append((pos, pos + len(g)))
        pos += len(g) + 1
    prefix = {}
    ok, instrs = walk(sec1)
    if ok:
        per_group, _ = _bucket_labels(extract_records(sec1, instrs)["label"], ranges, pos)
        for gi, sl in per_group.items():
            pl = _clean_prefix_len(sl)
            if pl is not None and pl < len(groups[gi]):
                prefix[gi] = pl
    out = {}
    for gi, g in enumerate(groups):
        lead, _t, _tr = _split_control_and_text(g[prefix.get(gi, 0):])
        run = []
        for w in lead:
            if w in VAR_INSERTS:
                run.append(w)
            else:
                break
        if run:
            out[gi] = run
    return out


def encode(english, enc):
    """English string -> glyph words exactly like build_v9's Step-4 encoder
    (' / ' and ' // ' -> FFFE, "[FXXX]" -> that control word)."""
    glyphs = []
    parts = [seg for page in english.split(' // ') for seg in page.split(' / ')]
    for pi, part in enumerate(parts):
        if pi > 0:
            glyphs.append(0xFFFE)
        for tok in CTRL_TOKEN_RE.split(part):
            if CTRL_TOKEN_RE.fullmatch(tok):
                glyphs.append(int(tok[1:5], 16))
            else:
                glyphs.extend(enc(ch) for ch in tok)
    return glyphs


def _main(path):
    import json
    sys.path.insert(0, os.path.join(ROOT, "tests"))
    import _helpers as H
    from patch_section1_offsets import inject_and_patch

    def enc(ch):
        return H.encode_english(ch)[0]

    props = json.load(open(path, encoding="utf-8"))
    by_res = collections.defaultdict(dict)
    bad_text = 0
    for p in props:
        en = p["english"]
        if "\n" in en or any(ord(c) > 127 for c in en):
            print("R%d G%d: ERROR non-ASCII or literal newline in english"
                  % (p["resource"], p["msg_index"]))
            bad_text += 1
        by_res[p["resource"]][p["msg_index"]] = en
    n_err = n_warn = 0
    raw_dir = os.path.join(ROOT, "extracted", "packdata_raw")
    with tempfile.TemporaryDirectory() as tmp:
        for res, msgs in sorted(by_res.items()):
            pristine = open(H.pristine_path(res, "02"), "rb").read()
            enc_msgs = {mi: encode(en, enc) for mi, en in msgs.items()}
            name, status = inject_and_patch(res, enc_msgs, raw_dir, tmp)
            if name is None:
                print("R%d: injector failed: %s" % (res, status))
                n_err += 1
                continue
            built = groups_of(open(os.path.join(tmp, name), "rb").read())
            pg = groups_of(pristine)
            allowed = stripped_leading_vars(pristine)
            for mi in sorted(msgs):
                errs, warns = audit_group(pg[mi], built[mi], allowed.get(mi, ()))
                for e in errs:
                    print("R%d G%d: ERROR %s" % (res, mi, e))
                for w in warns:
                    print("R%d G%d: warn  %s" % (res, mi, w))
                n_err += len(errs)
                n_warn += len(warns)
    print("audited %d proposals: %d errors, %d warnings"
          % (len(props), n_err + bad_text, n_warn))
    return 1 if (n_err + bad_text) else 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1]))
