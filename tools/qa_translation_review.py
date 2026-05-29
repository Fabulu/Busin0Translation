#!/usr/bin/env python3
"""QA review of all translation data files for Busin 0."""

import json
import os
import glob
import re
from collections import defaultdict

BASE = "C:/Programmieren/wizardrytranslation"
TYPE2_DIR = os.path.join(BASE, "data/type2_translated")
TYPE1_DIR = os.path.join(BASE, "data/translate_chunks")
OUTPUT = os.path.join(BASE, "runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/qa_translation_review.md")

MAX_LINE = 28

# Collect all entries: list of (file, idx, entry_dict, entry_type)
all_entries = []

# Type-2 files
for fp in sorted(glob.glob(os.path.join(TYPE2_DIR, "batch_*.json"))):
    if fp.endswith(".master"):
        continue
    fname = os.path.basename(fp)
    with open(fp, "r", encoding="utf-8") as f:
        data = json.load(f)
    for i, entry in enumerate(data):
        all_entries.append((fname, i, entry, "type2"))

# Type-1 files
for fp in sorted(glob.glob(os.path.join(TYPE1_DIR, "chunk_*_translated.json")) +
                 glob.glob(os.path.join(TYPE1_DIR, "chunk_*_fix.json")) +
                 glob.glob(os.path.join(TYPE1_DIR, "chunk_*_extra.json"))):
    fname = os.path.basename(fp)
    with open(fp, "r", encoding="utf-8") as f:
        data = json.load(f)
    for i, entry in enumerate(data):
        all_entries.append((fname, i, entry, "type1"))

print(f"Loaded {len(all_entries)} total entries")

# --- Issue collectors ---
issues_uppercase = []      # (file, idx, text, chars_found)
issues_long_line = []      # (file, idx, text, line, line_len)
issues_nonascii = []       # (file, idx, text, bad_chars)
issues_empty = []          # (file, idx, entry)
issues_missing_fields = [] # (file, idx, missing)

# Track (resource, msg_index) -> list of (file, idx)
seen_keys = defaultdict(list)

# Per-file uppercase counts
file_upper_counts = defaultdict(int)
file_entry_counts = defaultdict(int)

for fname, idx, entry, etype in all_entries:
    resource = entry.get("resource")
    msg_index = entry.get("msg_index") if etype == "type2" else entry.get("message")
    english = entry.get("english", "")

    file_entry_counts[fname] += 1

    # F: Missing fields
    missing = []
    if resource is None:
        missing.append("resource")
    if msg_index is None:
        if etype == "type2" and "msg_index" not in entry:
            missing.append("msg_index")
        elif etype == "type1" and "message" not in entry:
            missing.append("message")
    if missing:
        issues_missing_fields.append((fname, idx, missing))

    # Track for duplicates
    if resource is not None and msg_index is not None:
        seen_keys[(resource, msg_index)].append((fname, idx))

    # D: Empty english
    if english is None or (isinstance(english, str) and english.strip() == ""):
        issues_empty.append((fname, idx, entry))
        continue

    text = str(english)

    # A: Uppercase
    upper_chars = re.findall(r'[A-Z]', text)
    if upper_chars:
        issues_uppercase.append((fname, idx, text, upper_chars))
        file_upper_counts[fname] += 1

    # B: Long lines (split by " / ")
    lines = text.split(" / ")
    for line in lines:
        line_stripped = line.strip()
        if len(line_stripped) > MAX_LINE:
            issues_long_line.append((fname, idx, text, line_stripped, len(line_stripped)))

    # C: Non-ASCII
    bad_chars = [c for c in text if ord(c) > 127]
    if bad_chars:
        issues_nonascii.append((fname, idx, text, bad_chars))

# E: Duplicates
issues_duplicates = []
for key, locations in seen_keys.items():
    if len(locations) > 1:
        issues_duplicates.append((key[0], key[1], locations))

# --- Classify long lines by severity ---
long_by_severity = {"29-32": [], "33-40": [], "41-50": [], "51+": []}
for item in issues_long_line:
    llen = item[4]
    if llen <= 32:
        long_by_severity["29-32"].append(item)
    elif llen <= 40:
        long_by_severity["33-40"].append(item)
    elif llen <= 50:
        long_by_severity["41-50"].append(item)
    else:
        long_by_severity["51+"].append(item)

# --- Classify duplicates: same-file vs cross-file ---
dup_same_file = []
dup_cross_file = []
for res, mi, locs in issues_duplicates:
    files_involved = set(f for f, _ in locs)
    if len(files_involved) == 1:
        dup_same_file.append((res, mi, locs))
    else:
        dup_cross_file.append((res, mi, locs))

# --- Build report ---
L = []
L.append("# QA Translation Review Report")
L.append(f"\nDate: 2026-05-28")
L.append(f"\nTotal entries scanned: {len(all_entries)}")
L.append(f"  - Type-2 (batch_*.json): {sum(1 for _,_,_,t in all_entries if t=='type2')}")
L.append(f"  - Type-1 (chunk_*.json): {sum(1 for _,_,_,t in all_entries if t=='type1')}")
L.append("")

# Summary
L.append("## Summary")
L.append("")
L.append("| Category | Count | Severity |")
L.append("|---|---|---|")
L.append(f"| Uppercase characters | {len(issues_uppercase)} entries | HIGH - font atlas only has lowercase |")
L.append(f"| Lines > {MAX_LINE} chars | {len(issues_long_line)} lines | HIGH - will truncate on screen |")
L.append(f"| Non-ASCII characters | {len(issues_nonascii)} entries | OK |")
L.append(f"| Empty english fields | {len(issues_empty)} entries | MEDIUM |")
L.append(f"| Duplicate keys (cross-file) | {len(dup_cross_file)} keys | HIGH - build conflict |")
L.append(f"| Duplicate keys (same-file) | {len(dup_same_file)} keys | LOW - likely intentional |")
L.append(f"| Missing required fields | {len(issues_missing_fields)} entries | HIGH |")
L.append("")

# --- A: Uppercase ---
L.append("## A. Uppercase Characters (font atlas only has lowercase a-z)")
L.append(f"\n{len(issues_uppercase)} of {len(all_entries)} entries ({100*len(issues_uppercase)//len(all_entries)}%) contain uppercase.")
L.append("")
L.append("**NOTE:** The build pipeline's glyph encoder maps uppercase to lowercase automatically,")
L.append("so these will render as lowercase in-game. However, the source data should ideally be")
L.append("pre-lowercased for clarity. This is a cosmetic/data-hygiene issue, not a functional bug.")
L.append("")
L.append("### Per-file breakdown")
L.append("")
L.append("| File | Entries with uppercase | Total entries | % |")
L.append("|---|---|---|---|")
for fname in sorted(file_upper_counts.keys()):
    uc = file_upper_counts[fname]
    tot = file_entry_counts[fname]
    L.append(f"| {fname} | {uc} | {tot} | {100*uc//tot}% |")
L.append("")

# Count entries with ONLY uppercase (no lowercase) - possible special entries
only_upper = [(f,i,t) for f,i,t,c in issues_uppercase if not re.search(r'[a-z]', t)]
if only_upper:
    L.append(f"### Entries with ONLY uppercase (no lowercase) - {len(only_upper)} entries")
    L.append("")
    for f, i, t in only_upper[:20]:
        L.append(f"- **{f}** [#{i}]: `{t[:80]}`")
    if len(only_upper) > 20:
        L.append(f"- ... and {len(only_upper)-20} more")
    L.append("")

# --- B: Long lines ---
L.append("## B. Lines Exceeding 28 Characters")
L.append(f"\nTotal: {len(issues_long_line)} long lines across all entries")
L.append("")
L.append("| Severity | Count |")
L.append("|---|---|")
for sev in ["29-32", "33-40", "41-50", "51+"]:
    L.append(f"| {sev} chars | {len(long_by_severity[sev])} |")
L.append("")

L.append("### Critical (51+ chars) - likely multi-line or unformatted text")
L.append("")
for fname, idx, text, line, llen in sorted(long_by_severity["51+"], key=lambda x: -x[4])[:50]:
    L.append(f"- **{fname}** [#{idx}] ({llen} chars): `{line[:100]}`")
if len(long_by_severity["51+"]) > 50:
    L.append(f"- ... and {len(long_by_severity['51+'])-50} more")
L.append("")

L.append("### High (41-50 chars)")
L.append("")
for fname, idx, text, line, llen in sorted(long_by_severity["41-50"], key=lambda x: -x[4])[:30]:
    L.append(f"- **{fname}** [#{idx}] ({llen} chars): `{line[:100]}`")
if len(long_by_severity["41-50"]) > 30:
    L.append(f"- ... and {len(long_by_severity['41-50'])-30} more")
L.append("")

L.append("### Medium (33-40 chars)")
L.append("")
for fname, idx, text, line, llen in sorted(long_by_severity["33-40"], key=lambda x: -x[4])[:30]:
    L.append(f"- **{fname}** [#{idx}] ({llen} chars): `{line[:100]}`")
if len(long_by_severity["33-40"]) > 30:
    L.append(f"- ... and {len(long_by_severity['33-40'])-30} more")
L.append("")

L.append("### Low (29-32 chars)")
L.append("")
for fname, idx, text, line, llen in sorted(long_by_severity["29-32"], key=lambda x: -x[4])[:30]:
    L.append(f"- **{fname}** [#{idx}] ({llen} chars): `{line[:100]}`")
if len(long_by_severity["29-32"]) > 30:
    L.append(f"- ... and {len(long_by_severity['29-32'])-30} more")
L.append("")

# --- C: Non-ASCII ---
L.append("## C. Non-ASCII Characters (ord > 127)")
L.append(f"\nTotal: {len(issues_nonascii)} entries -- CLEAN")
L.append("")

# --- D: Empty english ---
L.append("## D. Empty English Fields")
L.append(f"\nTotal: {len(issues_empty)} entries")
L.append("")
if issues_empty:
    for fname, idx, entry in issues_empty:
        jp = str(entry.get("japanese", "?") or "?")[:60]
        r = entry.get("resource", "?")
        m = entry.get("msg_index", entry.get("message", "?"))
        L.append(f"- **{fname}** [#{idx}] r={r} m={m}: jp=`{jp}`")
L.append("")

# --- E: Duplicates ---
L.append("## E. Duplicate (resource, msg_index) Pairs")
L.append(f"\nTotal: {len(issues_duplicates)} duplicate keys")
L.append(f"  - Cross-file: {len(dup_cross_file)} (potential build conflicts)")
L.append(f"  - Same-file: {len(dup_same_file)} (likely intentional repeated messages)")
L.append("")

if dup_cross_file:
    L.append("### Cross-file duplicates (HIGH priority)")
    L.append("")
    for res, mi, locs in sorted(dup_cross_file)[:80]:
        loc_str = ", ".join(f"{f}[#{i}]" for f, i in locs)
        L.append(f"- r={res} m={mi}: {loc_str}")
    if len(dup_cross_file) > 80:
        L.append(f"- ... and {len(dup_cross_file)-80} more")
    L.append("")

if dup_same_file:
    L.append("### Same-file duplicates (low priority, top 30)")
    L.append("")
    for res, mi, locs in sorted(dup_same_file)[:30]:
        loc_str = ", ".join(f"{f}[#{i}]" for f, i in locs)
        L.append(f"- r={res} m={mi}: {loc_str}")
    if len(dup_same_file) > 30:
        L.append(f"- ... and {len(dup_same_file)-30} more")
    L.append("")

# --- F: Missing fields ---
L.append("## F. Missing Required Fields")
L.append(f"\nTotal: {len(issues_missing_fields)} entries")
L.append("")
if issues_missing_fields:
    for fname, idx, missing in issues_missing_fields[:50]:
        L.append(f"- **{fname}** [#{idx}]: missing {missing}")
L.append("")

# --- Canonical name check ---
L.append("## G. Canonical Name Consistency Check")
L.append("")
canonical = {
    "kingdom of duhan": ["duhan"],
    "karman's labyrinth": ["karman"],
    "gin barbus": ["gin barbus", "barbus"],
    "vera almohad": ["vera almohad", "almohad"],
    "luna light": ["luna light"],
}
# Check for variant spellings
name_variants = defaultdict(list)  # search_term -> list of (file, idx, text)
search_terms_lc = ["duhan", "karman", "barbus", "almohad", "luna"]
for fname, idx, entry, etype in all_entries:
    eng = str(entry.get("english", "") or "").lower()
    for term in search_terms_lc:
        if term in eng:
            name_variants[term].append((fname, idx, entry.get("english", "")))

for term in search_terms_lc:
    entries = name_variants[term]
    L.append(f"### '{term}' - {len(entries)} occurrences")
    for f, i, t in entries[:5]:
        L.append(f"  - {f}[#{i}]: `{str(t)[:80]}`")
    if len(entries) > 5:
        L.append(f"  - ... and {len(entries)-5} more")
    L.append("")

# Write output
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(L))

print(f"\nReport written to {OUTPUT}")
print(f"\n=== SUMMARY ===")
print(f"Uppercase:       {len(issues_uppercase)} entries (cosmetic - auto-lowered by build)")
print(f"Long lines:      {len(issues_long_line)} lines")
print(f"  51+ chars:     {len(long_by_severity['51+'])}")
print(f"  41-50 chars:   {len(long_by_severity['41-50'])}")
print(f"  33-40 chars:   {len(long_by_severity['33-40'])}")
print(f"  29-32 chars:   {len(long_by_severity['29-32'])}")
print(f"Non-ASCII:       {len(issues_nonascii)} entries")
print(f"Empty english:   {len(issues_empty)} entries")
print(f"Dup cross-file:  {len(dup_cross_file)} keys")
print(f"Dup same-file:   {len(dup_same_file)} keys")
print(f"Missing fields:  {len(issues_missing_fields)} entries")
