"""
Dialogue Overflow Audit for Busin 0 Type-2 Messages
Scans all batch_*.json files for lines exceeding 18 chars and pages exceeding 3 lines.
"""
import json, glob, os, textwrap
from collections import defaultdict

DATA_DIR = "C:/Programmieren/wizardrytranslation/data/type2_translated"
OUT_FILE = "C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/dialogue_overflow_audit.md"

MAX_LINE_CHARS = 18
MAX_LINES_PER_PAGE = 3

# Tags to skip
SKIP_PREFIXES = ("[DATA]", "[LAYOUT]", "[BINARY]", "[EMPTY]", "[CONTROL]", "[UNKNOWN]")

def analyze_entry(entry):
    eng = entry.get("english", "")
    if not eng or not eng.strip():
        return None
    for pfx in SKIP_PREFIXES:
        if eng.strip().startswith(pfx):
            return None

    # Split by " / " for line breaks
    lines = eng.split(" / ")

    longest_line = 0
    long_lines = []  # (line_idx, length, text)
    for i, line in enumerate(lines):
        ln = len(line)
        if ln > longest_line:
            longest_line = ln
        if ln > MAX_LINE_CHARS:
            long_lines.append((i, ln, line))

    total_lines = len(lines)
    too_many_lines = total_lines > MAX_LINES_PER_PAGE

    if not long_lines and not too_many_lines:
        return None

    return {
        "resource": entry.get("resource"),
        "msg_index": entry.get("msg_index"),
        "english": eng,
        "total_lines": total_lines,
        "longest_line": longest_line,
        "long_lines": long_lines,
        "too_many_lines": too_many_lines,
    }

def propose_fix(text, max_chars=MAX_LINE_CHARS, max_lines=MAX_LINES_PER_PAGE):
    """Attempt to reflow text to fit constraints."""
    lines = text.split(" / ")
    new_lines = []
    for line in lines:
        if len(line) <= max_chars:
            new_lines.append(line)
        else:
            # Word-wrap this line
            words = line.split()
            current = ""
            for w in words:
                if current and len(current) + 1 + len(w) > max_chars:
                    new_lines.append(current)
                    current = w
                else:
                    current = (current + " " + w).strip()
            if current:
                new_lines.append(current)

    # Add page breaks if needed (insert marker every max_lines lines)
    result_lines = []
    for i, l in enumerate(new_lines):
        if i > 0 and i % max_lines == 0:
            result_lines.append("[PAGE BREAK]")
        result_lines.append(l)

    return " / ".join(result_lines).replace(" / [PAGE BREAK] / ", " / [PAGE BREAK] / ")

# Main scan
all_issues = []
batch_stats = {}
total_entries = 0
total_translated = 0

batch_files = sorted(glob.glob(os.path.join(DATA_DIR, "batch_*.json")))
# Exclude .master files
batch_files = [f for f in batch_files if not f.endswith(".master")]

for bf in batch_files:
    fname = os.path.basename(bf)
    with open(bf, "r", encoding="utf-8") as f:
        data = json.load(f)

    batch_issues = []
    batch_total = len(data)
    batch_translated = 0

    for entry in data:
        total_entries += 1
        eng = entry.get("english", "")
        if eng and eng.strip() and not any(eng.strip().startswith(p) for p in SKIP_PREFIXES):
            batch_translated += 1
            total_translated += 1

        result = analyze_entry(entry)
        if result:
            result["file"] = fname
            batch_issues.append(result)
            all_issues.append(result)

    batch_stats[fname] = {
        "total": batch_total,
        "translated": batch_translated,
        "issues": len(batch_issues),
        "line_overflow": sum(1 for i in batch_issues if i["long_lines"]),
        "page_overflow": sum(1 for i in batch_issues if i["too_many_lines"]),
    }

# Compute statistics
line_overflow_entries = [i for i in all_issues if i["long_lines"]]
page_overflow_entries = [i for i in all_issues if i["too_many_lines"]]

# Length distribution for overflowing lines
length_dist = defaultdict(int)
for issue in all_issues:
    for _, ln, _ in issue["long_lines"]:
        length_dist[ln] += 1

# Sort worst offenders
by_longest = sorted(all_issues, key=lambda x: x["longest_line"], reverse=True)
by_most_lines = sorted(all_issues, key=lambda x: x["total_lines"], reverse=True)

# Generate report
lines_out = []
def w(s=""):
    lines_out.append(s)

w("# Dialogue Overflow Audit Report")
w(f"**Date:** 2026-05-28")
w(f"**Constraints:** {MAX_LINE_CHARS} chars/line, {MAX_LINES_PER_PAGE} lines/page")
w()
w("## Summary")
w()
w(f"- **Total entries scanned:** {total_entries}")
w(f"- **Translated entries:** {total_translated}")
w(f"- **Entries with ANY line > {MAX_LINE_CHARS} chars:** {len(line_overflow_entries)}")
w(f"- **Entries with > {MAX_LINES_PER_PAGE} lines (page overflow):** {len(page_overflow_entries)}")
w(f"- **Entries with BOTH issues:** {sum(1 for i in all_issues if i['long_lines'] and i['too_many_lines'])}")
w(f"- **Total problem entries:** {len(all_issues)}")
w(f"- **Clean entries:** {total_translated - len(all_issues)}")
w(f"- **Overflow rate:** {len(all_issues)/max(total_translated,1)*100:.1f}%")
w()

w("## Line Length Distribution (overflowing lines only)")
w()
w("| Chars | Count |")
w("|-------|-------|")
for ln in sorted(length_dist.keys()):
    w(f"| {ln} | {length_dist[ln]} |")
w()

# Bucket summary
bucket_19_20 = sum(v for k,v in length_dist.items() if 19 <= k <= 20)
bucket_21_25 = sum(v for k,v in length_dist.items() if 21 <= k <= 25)
bucket_26_30 = sum(v for k,v in length_dist.items() if 26 <= k <= 30)
bucket_31plus = sum(v for k,v in length_dist.items() if k >= 31)
w("**Buckets:**")
w(f"- 19-20 chars (minor, 1-2 chars over): {bucket_19_20} lines")
w(f"- 21-25 chars (moderate, 3-7 chars over): {bucket_21_25} lines")
w(f"- 26-30 chars (severe, 8-12 chars over): {bucket_26_30} lines")
w(f"- 31+ chars (critical, 13+ chars over): {bucket_31plus} lines")
w()

w("## Page Overflow Distribution")
w()
line_count_dist = defaultdict(int)
for issue in page_overflow_entries:
    line_count_dist[issue["total_lines"]] += 1
w("| Lines | Count |")
w("|-------|-------|")
for lc in sorted(line_count_dist.keys()):
    w(f"| {lc} | {line_count_dist[lc]} |")
w()

w("## Breakdown by Batch File")
w()
w("| File | Translated | Line Overflow | Page Overflow | Total Issues |")
w("|------|-----------|---------------|---------------|-------------|")
for fname in sorted(batch_stats.keys()):
    s = batch_stats[fname]
    w(f"| {fname} | {s['translated']} | {s['line_overflow']} | {s['page_overflow']} | {s['issues']} |")
w()

w("## Top 50 Worst Offenders (by longest line)")
w()
for rank, issue in enumerate(by_longest[:50], 1):
    w(f"### #{rank}: R{issue['resource']} msg {issue['msg_index']} ({issue['file']})")
    w(f"- **Longest line:** {issue['longest_line']} chars")
    w(f"- **Total lines:** {issue['total_lines']}")
    w(f"- **Original:**")
    w(f"```")
    # Show with line markers
    parts = issue["english"].split(" / ")
    for i, p in enumerate(parts):
        marker = " <<<OVER" if len(p) > MAX_LINE_CHARS else ""
        w(f"  L{i+1} [{len(p):2d}]: {p}{marker}")
    w(f"```")
    # Propose fix
    fix = propose_fix(issue["english"])
    fix_parts = fix.split(" / ")
    still_over = any(len(p) > MAX_LINE_CHARS for p in fix_parts if p != "[PAGE BREAK]")
    w(f"- **Proposed fix** {'(still has overflow - needs manual edit)' if still_over else '(fits)'}:")
    w(f"```")
    for i, p in enumerate(fix_parts):
        if p == "[PAGE BREAK]":
            w(f"  --- PAGE BREAK ---")
        else:
            marker = " <<<STILL OVER" if len(p) > MAX_LINE_CHARS else ""
            w(f"  L{i+1} [{len(p):2d}]: {p}{marker}")
    w(f"```")
    w()

w("## Top 20 Page Overflow Offenders (by line count)")
w()
shown = 0
for issue in by_most_lines:
    if not issue["too_many_lines"]:
        continue
    shown += 1
    if shown > 20:
        break
    w(f"### R{issue['resource']} msg {issue['msg_index']} ({issue['file']})")
    w(f"- **Lines:** {issue['total_lines']}")
    w(f"- **Longest line:** {issue['longest_line']} chars")
    w(f"- **Text:**")
    w(f"```")
    parts = issue["english"].split(" / ")
    for i, p in enumerate(parts):
        marker = " <<<OVER" if len(p) > MAX_LINE_CHARS else ""
        w(f"  L{i+1} [{len(p):2d}]: {p}{marker}")
    w(f"```")
    w()

w("---")
w("*End of audit report*")

report = "\n".join(lines_out)
with open(OUT_FILE, "w", encoding="utf-8") as f:
    f.write(report)

# Also print key stats to stdout
print(f"=== DIALOGUE OVERFLOW AUDIT COMPLETE ===")
print(f"Total entries: {total_entries}")
print(f"Translated: {total_translated}")
print(f"Line overflow (>{MAX_LINE_CHARS} chars): {len(line_overflow_entries)} entries")
print(f"Page overflow (>{MAX_LINES_PER_PAGE} lines): {len(page_overflow_entries)} entries")
print(f"Total problem entries: {len(all_issues)}")
print(f"Overflow rate: {len(all_issues)/max(total_translated,1)*100:.1f}%")
print(f"\nLength distribution (overflowing lines):")
for ln in sorted(length_dist.keys()):
    print(f"  {ln} chars: {length_dist[ln]} lines")
print(f"\nReport written to: {OUT_FILE}")
