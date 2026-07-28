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
    "test_stale_display_offsets",
    "test_island_label_sweep",
    "test_line_width",
    "test_dialogue_rewrap",
    "test_narration_wrap",
    "test_narration_overflow",
    "test_narration_centering",
    "test_narration_left_align",
    "test_narration_pad_map",
    "test_request_body_reserve",
    "test_request_proportional_patch25",
    "test_r1203_cap",
    "test_no_auto_pagebreak",
    "test_pipeline_rules",
    "test_r46_board",
    "test_r39_quests",
    "test_r39_spell_desc_alignment",
    "test_r39_title_table",
    "test_r39_section_table",
    "test_r39_request_wrap",
    "test_r39_client_cap",
    "test_r1193_narration",
    "test_iso_level",
    "test_packdata_overflow",
    "test_v86_strips",
    "test_glyph_metrics_sync",
    "test_r2100_metrics_source",
    "test_chargen_cave_imports_metrics",
    "test_chargen_race_nudge_patch28",
    "test_chargen_lsh_patch29",
    "test_chargen_sidebar_patch30",
    "test_chargen_lsh_patch31",
    "test_chargen_spacing",
    "test_chargen_class_descriptions",
    "test_chargen_centering",
    "test_chargen_diag_guard",
    "test_name_consistency",
    "test_exe_sjis_strings",
    "test_reloc_caves_installed",
    "test_cave_semantics",
    "test_shrink_equivalence",
    "test_r47_built_output",
    "test_janken_tremble",
    "test_r34_name_budget",
    "test_r2138_containment",
    "test_pill_widen",
    "test_banner_widget_pristine",
    "test_menu_record_image_slots",
    "test_optione_arena",
    "test_dialogue_wrap_force",
    "test_regress_harness",
    "test_v192_spell_quest_fixes",
    "test_issue40_name_reconciliation",
    "test_v195_item_name_divergence",
    "test_v196_reward_ritual_rcveq",
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
    # Release gate (master-audit finding #7): a SKIP means a tier's inputs were
    # absent -- exactly the mechanism that let the ISO tier stay dead for ~70
    # builds. For a release candidate, run with BUSIN_RELEASE=1: every SKIP is
    # then a failure, so a wiped build/ dir can never produce a green release.
    if os.environ.get("BUSIN_RELEASE") and n_skip:
        print("\nRESULT: FAIL -- BUSIN_RELEASE=1 and %d test(s) SKIPPED. A release "
              "run must exercise every tier (build outputs + ISO present)." % n_skip)
        return 1
    print("\nRESULT: OK%s" % (" (some tiers skipped)" if n_skip else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
