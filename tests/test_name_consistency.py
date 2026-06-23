#!/usr/bin/env python3
"""
test_name_consistency.py -- gate for the T6 name-consistency audit (P6).

The dialogue body text is normalized toward the canonical name spellings in
data/name_labels.json by tools/audit_name_consistency.py.  This module is the
regression gate: it FAILS if any known variant token reappears in the shipped
data, and it pins the superstring non-corruption invariants (Webster stays a
distinct character; "hysterical"/"revelation" are never mangled by the \b
replace).

It imports tools/audit_name_consistency as the single source of truth for the
CANON map, the TARGETS list and the variant_regex primitive -- the test never
re-defines the regex, so the apply tool and the gate can never desync.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import main_exit  # noqa: E402  (path insert first)

# _helpers puts tools/ on sys.path; import the audit tool as SoT.
import audit_name_consistency as audit  # noqa: E402


def _read(path):
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


# Files known to contain the distinct character "Webster" (must survive).
_WEBSTER_FILES = {
    "batch_01.json",
    "batch_03.json",
    "batch_04.json",
    "batch_05.json",
    "batch_06.json",
    "batch_09.json",
    "batch_r1198.json",
}


def test_all_targets_present():
    """Every audited data file is checked in and present."""
    missing = [p for p in audit.TARGETS if not os.path.isfile(p)]
    assert not missing, "audit TARGETS missing: %s" % ", ".join(
        os.path.relpath(p, audit.ROOT) for p in missing
    )


def test_no_remaining_variants():
    """No known variant token survives in any target -- the core gate."""
    offenders = []
    for path in audit.TARGETS:
        rem = audit.audit(_read(path))
        if rem:
            rel = os.path.relpath(path, audit.ROOT)
            for variant, cnt in sorted(rem.items()):
                offenders.append(
                    "%s: %s x%d (-> %s)" % (rel, variant, cnt, audit.CANON[variant])
                )
    assert not offenders, (
        "known name variants reappeared (run tools/audit_name_consistency.py "
        "--apply): %s" % "; ".join(offenders)
    )


def test_no_superstring_corruption():
    """The \\b replace must never mangle hysterical/revelation/Webster."""
    issues = []
    bad_hyst = re.compile(r"hyst[Ee]rikal")
    bad_rev = re.compile(r"re[Vv]eration")
    webster = re.compile(r"\bWebster\b")
    for path in audit.TARGETS:
        rel = os.path.relpath(path, audit.ROOT)
        text = _read(path)
        if bad_hyst.search(text):
            issues.append("%s: corrupted 'hysterical' -> hyst*rikal" % rel)
        if bad_rev.search(text):
            issues.append("%s: corrupted 'revelation' -> re*eration" % rel)
        if os.path.basename(path) in _WEBSTER_FILES and not webster.search(text):
            issues.append("%s: distinct 'Webster' vanished (wrongly merged?)" % rel)
    assert not issues, "; ".join(issues)


def test_canonical_present_where_expected():
    """A few canonical tokens must appear -- guards against a silent no-op apply."""
    checks = [
        ("batch_01.json", "Wesbell"),
        ("batch_03.json", "Belgrano"),
        ("batch_03.json", "Pipin"),
        ("batch_02.json", "Melanie"),
        ("batch_08.json", "Turgot"),
        ("batch_07.json", "Erika"),
    ]
    by_name = {os.path.basename(p): p for p in audit.TARGETS}
    issues = []
    for fname, token in checks:
        text = _read(by_name[fname])
        if not re.search(r"\b" + re.escape(token) + r"\b", text):
            issues.append("%s: expected canonical '%s' absent" % (fname, token))
    assert not issues, "; ".join(issues)


def test_audit_script_is_idempotent():
    """Re-applying the canon map to the shipped data is a no-op (converged)."""
    offenders = []
    for path in audit.TARGETS:
        _new, n = audit.apply_to_text(_read(path))
        if n:
            offenders.append("%s: %d further changes" % (os.path.relpath(path, audit.ROOT), n))
    assert not offenders, (
        "name normalization not converged in checked-in data: %s"
        % "; ".join(offenders)
    )


TESTS = [
    test_all_targets_present,
    test_no_remaining_variants,
    test_no_superstring_corruption,
    test_canonical_present_where_expected,
    test_audit_script_is_idempotent,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_name_consistency")
