#!/usr/bin/env python3
"""
audit_name_consistency.py -- whole-word name normalization toward name_labels.json.

The glyph-stream NAME SLOTS (the 0x14 name islands decoded through
data/name_labels.json) are already canonical; only the ASCII *body* text of the
dialogue diverged into ~24 variant spellings (~258 occurrences).  This is the
"name slot vs dialogue disagree" bug.  This tool normalizes the body text toward
the canonical spelling in data/name_labels.json.

It is the SINGLE SOURCE OF TRUTH for both the canonical map (CANON) and the
replacement primitive (variant_regex):

    re.sub(r'\b' + re.escape(variant) + r'\b', canonical, text)   # case-sensitive

The word-boundary (\b) anchoring at BOTH ends is load-bearing and prevents the
known superstring collisions:
  * Erica\b  vs "hystERICAl"  -> "hysterical" untouched (no boundary mid-word)
  * Vela\b   vs "reVELAtion"  -> "revelation" untouched
  * Turgo\b  vs "Turgot"/"Turgott" -> NOT matched (no boundary after "Turgo")
  * Romy\b   matches inside "Romy's" (apostrophe is a non-word char) -> "Romi's"
  * Webster  is NOT a variant token -> stays a distinct character, never merged.

Usage:
    python tools/audit_name_consistency.py            # audit-only, exit 1 if any
    python tools/audit_name_consistency.py --check     # alias of default audit
    python tools/audit_name_consistency.py --apply     # rewrite files in place

The apply is a raw-text re.sub over the whole file (JSON is NOT re-serialized),
so key order, indentation and per-file line endings are preserved byte-for-byte;
the only deltas are the name characters.  The apply is idempotent.
"""

import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T2_DIR = os.path.join(ROOT, "data", "type2_translated")
CHUNK_DIR = os.path.join(ROOT, "data", "translate_chunks")

# ── Canonical map: variant -> canonical (case-sensitive, whole-word) ──────────
# Ground truth = data/name_labels.json (every canonical token present there).
CANON = {
    "Wezbel": "Wesbell",
    "Wezbell": "Wesbell",
    "Wesbel": "Wesbell",
    "Vela": "Vera",
    "Romy": "Romi",
    "Roomi": "Romi",
    "Layman": "Raiman",
    "Beltan": "Bertin",
    "Kunnar": "Kunnal",  # canon flipped 2026-07-09: guide uses Kunnal 54:1
    "Melarnie": "Melanie",
    "Merani": "Melanie",
    "Melaanie": "Melanie",
    "Belgradno": "Belgrano",
    "Bergran": "Belgrano",
    "Pippin": "Pipin",
    "Poppo": "Popo",
    "Conde": "Konde",
    "Eerika": "Erika",
    "Erica": "Erika",
    "Frieda": "Frieder",
    "Shimzon": "Simzon",
    "Fuke": "Fouquet",
    "Turgo": "Turgot",
}

# Corruption sentinels -- superstrings the \b-anchored replace MUST leave intact.
SUPERSTRINGS = ["hysterical", "revelation", "Webster", "Turgot", "Turgott"]

# Explicit target list -- NEVER glob '*.json' (data/type2_translated also holds
# *.json.master / *.json.bak siblings that must not be touched).
TARGETS = [
    os.path.join(T2_DIR, "batch_01.json"),
    os.path.join(T2_DIR, "batch_02.json"),
    os.path.join(T2_DIR, "batch_03.json"),
    os.path.join(T2_DIR, "batch_04.json"),
    os.path.join(T2_DIR, "batch_05.json"),
    os.path.join(T2_DIR, "batch_06.json"),
    os.path.join(T2_DIR, "batch_07.json"),
    os.path.join(T2_DIR, "batch_08.json"),
    os.path.join(T2_DIR, "batch_09.json"),
    os.path.join(T2_DIR, "batch_r1198.json"),
    os.path.join(T2_DIR, "batch_r39_equip_a.json"),
    os.path.join(T2_DIR, "batch_r39_equip_b.json"),
    os.path.join(CHUNK_DIR, "chunk_r34_fix.json"),
]


# ── The shared replacement primitive ─────────────────────────────────────────
_REGEX_CACHE = {}


def variant_regex(variant):
    """Compiled case-sensitive whole-word matcher for one variant token."""
    rx = _REGEX_CACHE.get(variant)
    if rx is None:
        rx = re.compile(r"\b" + re.escape(variant) + r"\b")
        _REGEX_CACHE[variant] = rx
    return rx


def apply_to_text(text):
    """Apply every CANON variant->canonical over `text`.

    Returns (new_text, n_changes).  Single-pass and idempotent: no canonical
    output is a longer variant key, so application order is irrelevant and a
    re-apply yields zero further changes.
    """
    n_changes = 0
    out = text
    for variant, canonical in CANON.items():
        out, n = variant_regex(variant).subn(canonical, out)
        n_changes += n
    return out, n_changes


def audit(text):
    """Return {variant: count} of REMAINING known variant matches in `text`."""
    remaining = {}
    for variant in CANON:
        c = len(variant_regex(variant).findall(text))
        if c:
            remaining[variant] = c
    return remaining


def _read(path):
    # newline='' disables universal-newline translation -> per-file CRLF/LF
    # preserved verbatim on write-back.
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def _write(path, text):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def cmd_apply():
    total_changes = 0
    total_delta = 0
    for path in TARGETS:
        rel = os.path.relpath(path, ROOT)
        if not os.path.isfile(path):
            print("  [MISSING] %s" % rel)
            continue
        text = _read(path)
        new_text, n = apply_to_text(text)
        delta = len(new_text.encode("utf-8")) - len(text.encode("utf-8"))
        if new_text != text:
            _write(path, new_text)
        total_changes += n
        total_delta += delta
        print("  %-44s %3d changes  %+d bytes" % (rel, n, delta))
    print("-" * 64)
    print("  TOTAL: %d changes, net byte delta %+d" % (total_changes, total_delta))
    return 0


def cmd_audit():
    any_remaining = False
    for path in TARGETS:
        rel = os.path.relpath(path, ROOT)
        if not os.path.isfile(path):
            print("  [MISSING] %s" % rel)
            any_remaining = True
            continue
        rem = audit(_read(path))
        if rem:
            any_remaining = True
            detail = ", ".join("%s=%d" % (k, v) for k, v in sorted(rem.items()))
            print("  [VARIANTS] %-40s %s" % (rel, detail))
        else:
            print("  [clean]    %s" % rel)
    if any_remaining:
        print("\nRESULT: known name variants remain -- run with --apply.")
        return 1
    print("\nRESULT: zero remaining known variants across all %d files." % len(TARGETS))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--apply", action="store_true", help="rewrite files in place")
    g.add_argument("--check", action="store_true", help="audit-only (default)")
    args = ap.parse_args(argv)
    if args.apply:
        return cmd_apply()
    return cmd_audit()


if __name__ == "__main__":
    sys.exit(main())
