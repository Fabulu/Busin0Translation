#!/usr/bin/env python3
"""
run_all.py -- run the full v85 regression suite.

Usage:  python tests/run_all.py

Runs every test module in-process, prints a PASS/FAIL/SKIP summary table and
exits 0 only when there are no failures.  SKIPs mean a tier's inputs are
absent (e.g. no build output / no ISO) -- they are not failures, but a
release candidate ISO must run with all three tiers present.
"""

import importlib
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _helpers

MODULES = [
    "test_sec1_disasm",
    "test_patch_section1",
    "test_choice_groups",
    "test_line_width",
    "test_no_auto_pagebreak",
    "test_pipeline_rules",
    "test_r46_board",
    "test_r39_quests",
    "test_r1193_narration",
    "test_iso_level",
    "test_v86_strips",
]


def main():
    t0 = time.time()
    all_results = []
    for mod_name in MODULES:
        print("\n=== %s ===" % mod_name)
        try:
            mod = importlib.import_module(mod_name)
        except Exception as e:
            all_results.append(
                (mod_name, "<import>", "FAIL", "%s: %s" % (type(e).__name__, e))
            )
            print("  [FAIL] <import> -- %s: %s" % (type(e).__name__, e))
            continue
        all_results.extend(_helpers.run_tests(mod.TESTS, mod_name))

    n_pass = sum(1 for r in all_results if r[2] == "PASS")
    n_skip = sum(1 for r in all_results if r[2] == "SKIP")
    n_fail = sum(1 for r in all_results if r[2] == "FAIL")

    print()
    print("=" * 78)
    print("  v85 REGRESSION SUITE SUMMARY")
    print("=" * 78)
    print("%-22s %-44s %s" % ("MODULE", "TEST", "RESULT"))
    print("-" * 78)
    for mod, test, status, detail in all_results:
        print("%-22s %-44s %s" % (mod, test, status))
        if status != "PASS" and detail:
            print("%-22s   -> %s" % ("", detail[:120]))
    print("-" * 78)
    print(
        "TOTAL: %d passed, %d skipped, %d FAILED   (%.1fs)"
        % (n_pass, n_skip, n_fail, time.time() - t0)
    )
    if n_fail:
        print("\nRESULT: FAIL -- do NOT ship this build.")
        return 1
    print("\nRESULT: OK%s" % (" (some tiers skipped)" if n_skip else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
