#!/usr/bin/env python3
"""Tests for PACKDATA.DIG extractor output."""
import json, os, random, struct, sys, collections

PACKDATA = r"C:/Programmieren/wizardrytranslation/extracted/PACKDATA.DIG"
RESOURCES = r"C:/Programmieren/wizardrytranslation/extracted/packdata_resources"
RAW_DIR = r"C:/Programmieren/wizardrytranslation/extracted/packdata_raw"
MANIFEST = os.path.join(RESOURCES, "manifest.json")
FINDINGS_DIR = r"C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260522-1932-initial-recon/subagents/impl05-tests"
FINDINGS = os.path.join(FINDINGS_DIR, "FINDINGS.md")
results = []

def report(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    msg = f"[{status}] {name}"
    if detail:
        msg += f" -- {detail}"
    print(msg)
    results.append((name, passed, detail))

with open(MANIFEST, "r") as f:
    manifest = json.load(f)
valid_entries = [e for e in manifest if "skipped" not in e]
outlier_entries = [e for e in manifest if e.get("skipped")]

# Test 1: File count
bin_files = [f for f in os.listdir(RESOURCES) if f.endswith(".bin")]
raw_files = [f for f in os.listdir(RAW_DIR) if f.endswith(".raw")]
report("File count (.bin)", len(bin_files) == 2881, f"found {len(bin_files)}, expected 2881")
report("File count (.raw)", len(raw_files) == 2881, f"found {len(raw_files)}, expected 2881")

# Test 2: Manifest integrity
report("Manifest total entries", len(manifest) == 2883, f"found {len(manifest)}, expected 2883")
outlier_indices = sorted([e["index"] for e in outlier_entries])
report("Manifest outlier indices", outlier_indices == [1370, 2100], f"found {outlier_indices}")

# Test 3: Payload verification (20 random)
random.seed(42)
sample_payload = random.sample(valid_entries, min(20, len(valid_entries)))
payload_ok = 0
payload_fail_details = []
with open(PACKDATA, "rb") as dig:
    for e in sample_payload:
        offset = e["sector_offset"] * 2048 + 16
        dig.seek(offset)
        data_from_dig = dig.read(e["payload_size"])
        bin_path = os.path.join(RESOURCES, e["filename"])
        with open(bin_path, "rb") as bf:
            data_from_bin = bf.read()
        if data_from_dig == data_from_bin:
            payload_ok += 1
        else:
            payload_fail_details.append(f"idx {e['index']}: mismatch (dig={len(data_from_dig)} bin={len(data_from_bin)})")
report("Payload verification (20 spot-checks)", payload_ok == len(sample_payload),
       f"{payload_ok}/{len(sample_payload)} matched" + ("; " + "; ".join(payload_fail_details) if payload_fail_details else ""))

# Test 4: Raw file verification (10 entries)
sample_raw = random.sample(valid_entries, min(10, len(valid_entries)))
raw_ok = 0
raw_fail_details = []
for e in sample_raw:
    raw_name = e["filename"].replace(".bin", ".raw")
    raw_path = os.path.join(RAW_DIR, raw_name)
    if not os.path.exists(raw_path):
        raw_fail_details.append(f"idx {e['index']}: raw file missing")
        continue
    raw_size = os.path.getsize(raw_path)
    expected_raw_size = e["sector_count"] * 2048
    with open(raw_path, "rb") as rf:
        header = rf.read(16)
    if len(header) < 16:
        raw_fail_details.append(f"idx {e['index']}: header too short")
        continue
    zero1 = struct.unpack_from("<I", header, 0)[0]
    payload_sz = struct.unpack_from("<I", header, 4)[0]
    zero2 = struct.unpack_from("<I", header, 12)[0]
    issues = []
    if raw_size != expected_raw_size:
        issues.append(f"size {raw_size} != expected {expected_raw_size}")
    if zero1 != 0:
        issues.append(f"bytes 0-4 = {zero1:#x} != 0")
    if payload_sz != e["payload_size"]:
        issues.append(f"payload_size {payload_sz} != manifest {e['payload_size']}")
    if zero2 != 0:
        issues.append(f"bytes 12-16 = {zero2:#x} != 0")
    if issues:
        raw_fail_details.append(f"idx {e['index']}: {'; '.join(issues)}")
    else:
        raw_ok += 1
report("Raw file verification (10 spot-checks)", raw_ok == len(sample_raw),
       f"{raw_ok}/{len(sample_raw)} passed" + ("; " + "; ".join(raw_fail_details) if raw_fail_details else ""))

# Test 5: Contiguity test
sorted_valid = sorted(valid_entries, key=lambda e: e["sector_offset"])
contig_ok = True
contig_breaks = []
for i in range(len(sorted_valid) - 1):
    end_sec = sorted_valid[i]["sector_offset"] + sorted_valid[i]["sector_count"]
    nxt = sorted_valid[i + 1]["sector_offset"]
    if end_sec != nxt:
        contig_ok = False
        contig_breaks.append(f"gap at idx {sorted_valid[i]['index']}->{sorted_valid[i+1]['index']}: end={end_sec} next={nxt}")
        if len(contig_breaks) >= 5:
            contig_breaks.append("...(truncated)")
            break
report("Contiguity", contig_ok, "; ".join(contig_breaks) if contig_breaks else "all entries contiguous")

# Test 6: Boundary test
file_size = os.path.getsize(PACKDATA)
first_offset = sorted_valid[0]["sector_offset"]
last_end = sorted_valid[-1]["sector_offset"] + sorted_valid[-1]["sector_count"]
last_end_bytes = last_end * 2048
report("First entry at sector 0x7D", first_offset == 0x7D, f"first sector_offset = {first_offset:#x}")
report("Last entry ends at file size", last_end_bytes == file_size,
       f"last_end={last_end_bytes} file_size={file_size} diff={file_size - last_end_bytes}")

# Test 7: Type distribution
type_counts = collections.Counter(e["type_code"] for e in valid_entries)
most_common_type = type_counts.most_common(1)[0]
report("Type 1 most common", most_common_type[0] == 1,
       f"most common: type {most_common_type[0]} ({most_common_type[1]}x); distribution: {dict(sorted(type_counts.items()))}")

# Test 8: No empty files
empty_bins = []
for e in valid_entries:
    bp = os.path.join(RESOURCES, e["filename"])
    if os.path.getsize(bp) == 0:
        empty_bins.append(e["filename"])
report("No empty .bin files", len(empty_bins) == 0,
       f"{len(empty_bins)} empty files" + (f": {empty_bins[:5]}" if empty_bins else ""))

# Test 9: Sub-header stride validation (50 random)
sample_stride = random.sample(valid_entries, min(50, len(valid_entries)))
stride_ok = 0
stride_fail = []
for e in sample_stride:
    expected_stride = e["type_code"] * 16
    if e["stride"] == expected_stride:
        stride_ok += 1
    else:
        stride_fail.append(f"idx {e['index']}: stride={e['stride']} expected={expected_stride} (type={e['type_code']})")
        if len(stride_fail) >= 5:
            stride_fail.append("...(truncated)")
            break
report("Sub-header stride = type_code * 16 (50 spot-checks)", stride_ok == len(sample_stride),
       f"{stride_ok}/{len(sample_stride)} matched" + ("; " + "; ".join(stride_fail) if stride_fail else ""))

# Test 10: Total size check
total_raw_size = sum(os.path.getsize(os.path.join(RAW_DIR, e["filename"].replace(".bin", ".raw"))) for e in valid_entries)
header_region = 256000
approx_total = total_raw_size + header_region
diff_pct = abs(approx_total - file_size) / file_size * 100
report("Total size approximation", diff_pct < 1.0,
       f"raw_total={total_raw_size} + header={header_region} = {approx_total}; actual={file_size}; diff={diff_pct:.2f}%")

# Summary
passed_count = sum(1 for _, p, _ in results if p)
total_count = len(results)
print()
print("=" * 60)
print(f"SUMMARY: {passed_count}/{total_count} tests passed")
print("=" * 60)

os.makedirs(FINDINGS_DIR, exist_ok=True)
with open(FINDINGS, "w") as f:
    f.write("# PACKDATA.DIG Extractor Test Results\n\n")
    f.write(f"**Date**: 2026-05-22\n")
    f.write(f"**Summary**: {passed_count}/{total_count} tests passed\n\n")
    f.write("| # | Test | Result | Details |\n")
    f.write("|---|------|--------|---------|\n")
    for i, (name, p, detail) in enumerate(results, 1):
        status = "PASS" if p else "FAIL"
        detail_escaped = detail.replace("|", "/")
        f.write(f"| {i} | {name} | {status} | {detail_escaped} |\n")
    f.write("\n## Notes\n\n")
    if passed_count < total_count:
        f.write("Some tests failed. Review details above for investigation.\n")
    else:
        f.write("All tests passed. Extractor output is consistent and verified.\n")

print(f"\nFindings written to {FINDINGS}")
sys.exit(0 if passed_count == total_count else 1)
