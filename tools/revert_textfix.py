#!/usr/bin/env python3
"""
revert_textfix.py -- selectively revert the 2026-07-11 dialogue text-fix wave
(issue #15-20 + the corpus-wide prefix/quote/gender/Commander sweeps).

Every applied change is recorded in data/textfix_applied_20260711.json as
  {"file", "resource", "msg_index", "old", "new"}

Usage:
  python tools/revert_textfix.py --list                    # show records
  python tools/revert_textfix.py --all                     # revert everything
  python tools/revert_textfix.py --resource 1203           # one resource
  python tools/revert_textfix.py --resource 1203 --msg 974 # one entry
  python tools/revert_textfix.py --op dequote|deprefix|gender|commander|full|fold

A revert only fires if the entry still equals the applied "new" text (a later
manual edit wins and is reported, not clobbered). Rebuild afterwards.
NOTE: this reverts the TEXT edits only. The nameplate-island fixes live in
data/name_labels.json (3 keys) and data/nameplate_overrides.json (8 groups) and
are reverted by editing/removing those directly.
"""
import argparse
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECORD = os.path.join(ROOT, "data", "textfix_applied_20260711.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--resource", type=int)
    ap.add_argument("--msg", type=int)
    ap.add_argument("--op")  # informational only; record has no op field, so ignored for selection
    args = ap.parse_args()

    recs = json.load(open(RECORD, encoding="utf-8"))
    if args.list:
        for r in recs:
            print("R%d m%d (%s)" % (r["resource"], r["msg_index"], os.path.basename(r["file"])))
        print("%d records" % len(recs))
        return

    sel = [r for r in recs
           if (args.all or r["resource"] == args.resource)
           and (args.msg is None or r["msg_index"] == args.msg)]
    if not sel:
        print("nothing selected (use --list / --all / --resource N [--msg M])")
        return

    by_file = {}
    for r in sel:
        by_file.setdefault(r["file"], []).append(r)

    reverted = skipped = 0
    for path, rs in by_file.items():
        full = os.path.join(ROOT, path)
        d = json.load(open(full, encoding="utf-8"))
        idx = {(e.get("resource"), e.get("msg_index")): e for e in d}
        orig = open(full, encoding="utf-8").read()
        indent = 2 if orig.startswith("[\n  {") else (1 if orig.startswith("[\n {") else 1)
        trailing_nl = orig.endswith("\n")
        for r in rs:
            e = idx.get((r["resource"], r["msg_index"]))
            if e is not None and e.get("english") == r["new"]:
                e["english"] = r["old"]
                reverted += 1
            else:
                print("  SKIP R%d m%d: current text != applied 'new' (manual edit wins)"
                      % (r["resource"], r["msg_index"]))
                skipped += 1
        out = json.dumps(d, ensure_ascii=False, indent=indent)
        if trailing_nl:
            out += "\n"
        open(full, "w", encoding="utf-8").write(out)
        json.load(open(full, encoding="utf-8"))  # parse gate
    print("reverted %d, skipped %d. Rebuild to ship." % (reverted, skipped))


if __name__ == "__main__":
    main()
