#!/usr/bin/env python3
"""
analyze_cdvd_log.py - Analyze PCSX2 emulog CDVD read entries.

Parses CDRead log lines from PCSX2's emulog.txt, maps each sector read
to a PACKDATA.DIG resource using the extraction manifest, and reports:
  - Which resources were loaded and in what order
  - Whether specific resources of interest (R1188, R1272, etc.) were accessed
  - The full timeline of disc reads

Usage:
    python tools/analyze_cdvd_log.py [--emulog <path>] [--after <timestamp>]

If --emulog is not given, uses the default PCSX2 log location.
"""

import re
import json
import sys
import os
import argparse
from collections import OrderedDict

BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
MANIFEST_PATH = os.path.join(BASE_DIR, "extracted", "packdata_resources", "manifest.json")

# PACKDATA.DIG starts at this ISO LBA (sector) on SLPM-65378
PACKDATA_ISO_LBA = 16029
PACKDATA_HEADER_SECTORS = 125  # TOC region = sectors 0..124 within PACKDATA

# Default emulog location for this machine
DEFAULT_EMULOG = os.path.expanduser(
    r"~\OneDrive - Berner Fachhochschule\Dokumente\PCSX2\logs\emulog.txt"
)

# Resources of special interest
RESOURCES_OF_INTEREST = {
    34:   "R34 (type-01 text block)",
    35:   "R35 (fixed-size inject)",
    38:   "R38 (sidebar/stat labels)",
    39:   "R39 (equipment data)",
    46:   "R46 (bulletin board)",
    47:   "R47 (bulletin board)",
    1188: "R1188 (name entry font atlas, 1024x1024 PSMT4)",
    1193: "R1193 (manual inject)",
    1272: "R1272 (main dialogue font atlas, 256x512 PSMT4)",
    2124: "R2124 (type-01 text)",
    2654: "R2654 (fixed-size inject)",
}

# CDRead log line pattern:
# [   21.1181] CDRead: Reading Sector 0000016 (001 Blocks of Size 2048) at Speed=4x(CAV) Spindle=83
CDREAD_RE = re.compile(
    r'^\[\s*(\d+\.\d+)\]\s+CDRead:\s+Reading\s+Sector\s+(\d+)\s+\((\d+)\s+Blocks'
)


def load_manifest():
    """Load the PACKDATA resource manifest and build a sector-range lookup."""
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        entries = json.load(f)

    resources = []
    for e in entries:
        if e.get("skipped"):
            continue
        iso_start = PACKDATA_ISO_LBA + e["sector_offset"]
        iso_end = iso_start + e["sector_count"]  # exclusive
        resources.append({
            "index": e["index"],
            "iso_start": iso_start,
            "iso_end": iso_end,
            "sector_count": e["sector_count"],
            "type_code": e["type_code"],
            "packdata_offset": e["sector_offset"],
        })

    # Sort by iso_start for binary search
    resources.sort(key=lambda r: r["iso_start"])
    return resources


def find_resource_for_sector(resources, sector):
    """Find which PACKDATA resource contains a given ISO sector, or None."""
    # Binary search
    lo, hi = 0, len(resources) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        r = resources[mid]
        if sector < r["iso_start"]:
            hi = mid - 1
        elif sector >= r["iso_end"]:
            lo = mid + 1
        else:
            return r
    return None


def classify_sector(resources, sector):
    """Classify a sector into a human-readable region."""
    # Check if it's in the PACKDATA header (TOC)
    pack_header_start = PACKDATA_ISO_LBA
    pack_header_end = PACKDATA_ISO_LBA + PACKDATA_HEADER_SECTORS
    if pack_header_start <= sector < pack_header_end:
        return "PACKDATA_TOC", None

    # Check if it maps to a specific resource
    r = find_resource_for_sector(resources, sector)
    if r is not None:
        return f"R{r['index']}", r

    # Check broad regions
    # PACKDATA ends around sector 426020; sectors beyond that are EXE/other files
    PACKDATA_END_LBA = PACKDATA_ISO_LBA + 410000  # approximate upper bound
    if sector < 16:
        return "ISO_SYSTEM_AREA", None
    elif sector < 257:
        return "ISO_PVD_AREA", None
    elif sector < 16029:
        return "ISO_FILESYSTEM", None
    elif sector >= PACKDATA_END_LBA:
        return "EXE_OR_OTHER_FILES", None
    elif sector >= PACKDATA_ISO_LBA:
        return "PACKDATA_GAP", None
    else:
        return "UNKNOWN", None


def parse_emulog(emulog_path, after_time=None):
    """Parse CDRead entries from the emulog."""
    reads = []
    with open(emulog_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            m = CDREAD_RE.match(line)
            if m:
                timestamp = float(m.group(1))
                sector = int(m.group(2))
                block_count = int(m.group(3))
                if after_time is not None and timestamp < after_time:
                    continue
                reads.append({
                    "time": timestamp,
                    "sector": sector,
                    "blocks": block_count,
                })
    return reads


def analyze(reads, resources):
    """Analyze the reads and produce a report."""
    lines = []
    lines.append("=" * 78)
    lines.append("CDVD READ ANALYSIS")
    lines.append("=" * 78)
    lines.append(f"Total CDRead entries: {len(reads)}")
    if reads:
        lines.append(f"Time range: {reads[0]['time']:.4f}s - {reads[-1]['time']:.4f}s")
    lines.append("")

    # Map each read to a resource/region
    resource_first_seen = OrderedDict()  # resource_label -> first timestamp
    resource_read_count = {}
    resource_sectors_read = {}
    toc_reads = []
    timeline = []

    for rd in reads:
        sector = rd["sector"]
        blocks = rd["blocks"]
        time = rd["time"]

        # Each read covers sector..sector+blocks-1
        # Classify by the START sector (most reads are contiguous within one resource)
        label, res = classify_sector(resources, sector)

        timeline.append((time, sector, blocks, label))

        if label not in resource_first_seen:
            resource_first_seen[label] = time
        resource_read_count[label] = resource_read_count.get(label, 0) + 1
        resource_sectors_read[label] = resource_sectors_read.get(label, 0) + blocks

        if label == "PACKDATA_TOC":
            toc_reads.append(rd)

    # ---- Section 1: Resource load order ----
    lines.append("-" * 78)
    lines.append("RESOURCE LOAD ORDER (first access time)")
    lines.append("-" * 78)
    for i, (label, first_time) in enumerate(resource_first_seen.items()):
        count = resource_read_count[label]
        sectors = resource_sectors_read[label]
        interest = ""
        # Check if this is a resource of interest
        if label.startswith("R") and label[1:].isdigit():
            ridx = int(label[1:])
            if ridx in RESOURCES_OF_INTEREST:
                interest = f"  *** {RESOURCES_OF_INTEREST[ridx]} ***"
        elif label == "PACKDATA_TOC":
            interest = "  *** PACKDATA header/TOC ***"
        lines.append(f"  {i+1:4d}. [{first_time:9.4f}s] {label:<30s} "
                      f"({count} reads, {sectors} sectors){interest}")
    lines.append("")

    # ---- Section 2: Resources of interest ----
    lines.append("-" * 78)
    lines.append("RESOURCES OF INTEREST - STATUS")
    lines.append("-" * 78)

    # PACKDATA TOC
    pack_toc_label = "PACKDATA_TOC"
    if pack_toc_label in resource_first_seen:
        lines.append(f"  PACKDATA TOC (LBA {PACKDATA_ISO_LBA}-{PACKDATA_ISO_LBA + PACKDATA_HEADER_SECTORS - 1}):")
        lines.append(f"    LOADED at {resource_first_seen[pack_toc_label]:.4f}s "
                      f"({resource_read_count[pack_toc_label]} reads, "
                      f"{resource_sectors_read[pack_toc_label]} sectors)")
    else:
        lines.append(f"  PACKDATA TOC: *** NOT READ ***")
    lines.append("")

    for ridx, desc in sorted(RESOURCES_OF_INTEREST.items()):
        label = f"R{ridx}"
        r = None
        for res in resources:
            if res["index"] == ridx:
                r = res
                break
        lba_range = ""
        if r:
            lba_range = f" (LBA {r['iso_start']}-{r['iso_end'] - 1}, {r['sector_count']} sectors)"

        if label in resource_first_seen:
            lines.append(f"  {desc}{lba_range}:")
            lines.append(f"    LOADED at {resource_first_seen[label]:.4f}s "
                          f"({resource_read_count[label]} reads, "
                          f"{resource_sectors_read[label]} sectors)")
        else:
            lines.append(f"  {desc}{lba_range}:")
            lines.append(f"    *** NOT READ ***")
    lines.append("")

    # ---- Section 3: Full timeline (condensed) ----
    lines.append("-" * 78)
    lines.append("FULL TIMELINE (condensed: consecutive reads to same resource merged)")
    lines.append("-" * 78)

    if timeline:
        prev_label = None
        group_start_time = 0
        group_start_sector = 0
        group_total_sectors = 0
        group_count = 0

        def flush_group():
            if prev_label is not None:
                lines.append(f"  [{group_start_time:9.4f}s] {prev_label:<30s} "
                              f"sector {group_start_sector:>7d}, "
                              f"{group_total_sectors:>5d} sectors "
                              f"({group_count} reads)")

        for time, sector, blocks, label in timeline:
            if label != prev_label:
                flush_group()
                prev_label = label
                group_start_time = time
                group_start_sector = sector
                group_total_sectors = blocks
                group_count = 1
            else:
                group_total_sectors += blocks
                group_count += 1

        flush_group()
    lines.append("")

    # ---- Section 4: Summary statistics ----
    lines.append("-" * 78)
    lines.append("SUMMARY")
    lines.append("-" * 78)
    total_sectors = sum(rd["blocks"] for rd in reads)
    total_bytes = total_sectors * 2048
    unique_resources = sum(1 for l in resource_first_seen if l.startswith("R") and l[1:].isdigit())
    lines.append(f"  Total disc reads:     {len(reads)}")
    lines.append(f"  Total sectors read:   {total_sectors} ({total_bytes:,} bytes, {total_bytes / 1024 / 1024:.1f} MB)")
    lines.append(f"  Unique PACKDATA resources accessed: {unique_resources}")
    lines.append(f"  PACKDATA TOC reads:   {resource_read_count.get('PACKDATA_TOC', 0)}")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Analyze PCSX2 CDVD read log")
    parser.add_argument("--emulog", default=DEFAULT_EMULOG,
                        help="Path to PCSX2 emulog.txt")
    parser.add_argument("--after", type=float, default=None,
                        help="Only analyze reads after this timestamp (seconds)")
    parser.add_argument("--output", default=None,
                        help="Write report to file (default: print to stdout)")
    args = parser.parse_args()

    if not os.path.isfile(args.emulog):
        print(f"ERROR: emulog not found at: {args.emulog}")
        print(f"Specify with --emulog <path>")
        sys.exit(1)

    print(f"Loading manifest from: {MANIFEST_PATH}")
    resources = load_manifest()
    print(f"  {len(resources)} PACKDATA resources mapped")

    print(f"Parsing emulog: {args.emulog}")
    reads = parse_emulog(args.emulog, after_time=args.after)
    print(f"  {len(reads)} CDRead entries found")

    if not reads:
        print("\nNo CDRead entries found in the emulog.")
        print("Make sure CdvdVerboseReads=true is set in PCSX2.ini and you booted a game.")
        sys.exit(0)

    report = analyze(reads, resources)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\nReport written to: {args.output}")
    else:
        print("\n" + report)


if __name__ == "__main__":
    main()
