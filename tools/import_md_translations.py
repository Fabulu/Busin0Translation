#!/usr/bin/env python3
"""
Import translations from markdown review files into the build pipeline's JSON format.

Reads untranslated_for_review.md and untranslated_type2_dialogue.md,
extracts entries with non-empty English translations, and writes them
as JSON files that the build pipeline auto-discovers.

Output:
  data/translate_chunks/chunk_md_import.json  — type-1 (R34-R49) entries
  data/type2_translated/batch_md_import.json  — type-2 dialogue entries
"""

import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MD_FILES = [
    os.path.join(BASE, "data", "untranslated_for_review.md"),
    os.path.join(BASE, "data", "untranslated_type2_dialogue.md"),
]

# Type-1 resources go into translate_chunks, type-2 into type2_translated
TYPE1_RESOURCES = set(range(34, 50)) | {2124, 2654}
TYPE2_OUTPUT = os.path.join(BASE, "data", "type2_translated", "batch_md_import.json")
TYPE1_OUTPUT = os.path.join(BASE, "data", "translate_chunks", "chunk_md_import.json")


def parse_md(filepath):
    """Parse a markdown translation file, yielding (resource, message, japanese, english) tuples."""
    if not os.path.exists(filepath):
        print(f"  SKIP: {filepath} not found")
        return

    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()

    resource = None
    message = None
    japanese = None
    english = None
    context = None

    for line in lines:
        line = line.rstrip("\n")

        # Header: ### R{num}:M{num} (context)
        m = re.match(r'^### R(\d+):M(\d+)\s*(?:\(([^)]*)\))?', line)
        if m:
            # Emit previous entry if complete
            if resource is not None and english and english.strip():
                yield resource, message, japanese, english, context
            resource = int(m.group(1))
            message = int(m.group(2))
            context = m.group(3) or ""
            japanese = None
            english = None
            continue

        # Japanese line
        if line.startswith("- Japanese: "):
            japanese = line[len("- Japanese: "):]
            continue

        # English line
        if line.startswith("- English: "):
            english = line[len("- English: "):]
            continue

    # Emit last entry
    if resource is not None and english and english.strip():
        yield resource, message, japanese, english, context


def main():
    type1_entries = []
    type2_entries = []
    skipped_garbled = 0
    skipped_translated = 0
    skipped_empty = 0

    for md_file in MD_FILES:
        print(f"Parsing: {md_file}")
        for resource, message, japanese, english, context in parse_md(md_file):
            # Skip garbled/empty/already-translated markers
            if "[GARBLED" in english or "[GARBLED" in (context or ""):
                skipped_garbled += 1
                continue
            if "[TRANSLATED]" in (context or ""):
                skipped_translated += 1
                continue
            if not english.strip() or english.strip() == "[EMPTY]":
                skipped_empty += 1
                continue

            entry = {
                "resource": resource,
                "message": message,
                "japanese": japanese or "",
                "english": english.strip(),
            }

            if resource in TYPE1_RESOURCES:
                type1_entries.append(entry)
            else:
                type2_entries.append(entry)

    print(f"\nParsed: {len(type1_entries)} type-1, {len(type2_entries)} type-2")
    print(f"Skipped: {skipped_garbled} garbled, {skipped_translated} already translated, {skipped_empty} empty")

    # Write type-1
    os.makedirs(os.path.dirname(TYPE1_OUTPUT), exist_ok=True)
    with open(TYPE1_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(type1_entries, f, ensure_ascii=False, indent=2)
    print(f"Wrote: {TYPE1_OUTPUT} ({len(type1_entries)} entries)")

    # Write type-2
    os.makedirs(os.path.dirname(TYPE2_OUTPUT), exist_ok=True)
    with open(TYPE2_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(type2_entries, f, ensure_ascii=False, indent=2)
    print(f"Wrote: {TYPE2_OUTPUT} ({len(type2_entries)} entries)")


if __name__ == "__main__":
    main()
