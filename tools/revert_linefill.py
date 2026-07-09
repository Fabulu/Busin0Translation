#!/usr/bin/env python3
"""
revert_linefill.py -- selectively revert the line-fill (rewrap) pass.

The line-fill pass (2026-07-09) re-wrapped under-filled dialogue lines for the
proportional-font box: SAME words, only ' / ' break positions moved. Every
applied change is recorded in data/linefill_applied_*.json as
  {"file": <batch file>, "resource": R, "msg_index": N,
   "old": "<text before>", "new": "<text after>"}

Usage:
  python tools/revert_linefill.py --list                       # show records
  python tools/revert_linefill.py --all                        # revert everything
  python tools/revert_linefill.py --resource 1207              # one resource
  python tools/revert_linefill.py --resource 1207 --msg 350    # one entry

Reverting swaps the entry's english back to "old" IN THE RECORDED FILE, but
only if it still equals "new" (a later manual edit wins and is reported, not
clobbered). Rebuild afterwards.
"""
import argparse
import glob
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_records():
    recs = []
    for p in sorted(glob.glob(os.path.join(ROOT, "data", "linefill_applied_*.json"))):
        recs.extend(json.load(open(p, encoding="utf-8")))
    return recs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--resource", type=int)
    ap.add_argument("--msg", type=int)
    args = ap.parse_args()

    recs = load_records()
    if args.list:
        for r in recs:
            print(f"R{r['resource']} m{r['msg_index']} ({os.path.basename(r['file'])})")
        print(f"{len(recs)} records")
        return

    sel = [r for r in recs
           if (args.all or r.get("resource") == args.resource)
           and (args.msg is None or r.get("msg_index") == args.msg)]
    if not sel:
        print("nothing selected (use --list / --all / --resource N [--msg M])")
        return

    by_file = {}
    for r in sel:
        by_file.setdefault(r["file"], []).append(r)

    reverted = skipped = 0
    for path, rs in by_file.items():
        full = os.path.join(ROOT, path)
        s = open(full, encoding="utf-8").read()
        for r in rs:
            oldlit = json.dumps(r["new"], ensure_ascii=False)
            newlit = json.dumps(r["old"], ensure_ascii=False)
            if s.count(oldlit) == 1:
                s = s.replace(oldlit, newlit, 1)
                reverted += 1
            else:
                print(f"  SKIP R{r['resource']} m{r['msg_index']}: current text "
                      f"no longer matches the applied rewrap (manual edit wins)")
                skipped += 1
        open(full, "w", encoding="utf-8").write(s)
        json.load(open(full, encoding="utf-8"))  # parse gate
    print(f"reverted {reverted}, skipped {skipped}. Rebuild to ship.")


if __name__ == "__main__":
    main()
