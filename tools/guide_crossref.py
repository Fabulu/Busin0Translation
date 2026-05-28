#!/usr/bin/env python3
"""
Guide Cross-Reference Tool
===========================
Matches English guide PDF text against partially-decoded Japanese dialogue
to infer unmapped glyphs.
"""

import json
import re
import sys
import os
from collections import Counter, defaultdict

BASE = r"C:\Programmieren\wizardrytranslation\data"
GUIDE_PATH = os.path.join(BASE, "guide_full_text.txt")
DIALOGUE_PATH = os.path.join(BASE, "type2_dialogue_corrected.json")
GLYPH_MAP_PATH = os.path.join(BASE, "msg_glyph_map.json")
OUTPUT_PATH = os.path.join(BASE, "guide_crossref_inferences.json")

NAME_MAPPINGS = {
    "\u30f4\u30a3\u30ac\u30fc": "Vigger",
    "\u30aa\u30fc\u30af": "Orc",
    "\u30aa\u30c0": "Oda",
    "\u30e2\u30c3\u30c8": "Mott",
    "\u30b8\u30f3": "Gin",
    "\u30c9\u30a5\u30fc\u30cf\u30f3": "Duhan",
    "\u30ab\u30eb\u30de\u30f3": "Karman",
    "\u30f4\u30a7\u30e9": "Vera",
    "\u30a2\u30eb\u30e2\u30a2\u30c3\u30c9": "Almohad",
    "\u30b7\u30e0\u30bd\u30f3": "Simson",
    "\u30e9\u30a4\u30de\u30f3": "Raiman",
    "\u30af\u30f3\u30ca\u30eb": "Kunnal",
    "\u30cf\u30f3\u30ca": "Hannah",
    "\u30d5\u30fc\u30b1": "Fouquet",
    "\u30eb\u30fc\u30b7\u30fc": "Lucy",
    "\u30a8\u30df\u30fc\u30ea\u30a2": "Emilia",
    "\u30ea\u30e5\u30fc\u30c8": "Lute",
    "\u30d5\u30c9\u30a6": "Fudou",
    "\u30d0\u30eb\u30d0\u30b9": "Barbus",
    "\u30f4\u30a7\u30ce\u30a2": "Venoa",
    "\u8ff7\u5bae": "labyrinth",
}

EN_TO_JP = {v.lower(): k for k, v in NAME_MAPPINGS.items()}
UNMAPPED_PAT = re.compile(r'\[([0-9A-Fa-f]{4})\]')

KNOWN_COMPOUNDS = {
    ("\u306e", "\u983c"): ("\u4f9d", 0.85, "\u4f9d\u983c (request)"),
    ("", "\u983c"): ("\u4f9d", 0.80, "\u4f9d\u983c (request)"),
    ("\u5831", ""): ("\u544a", 0.80, "\u5831\u544a (report)"),
    ("", "\u544a"): ("\u5831", 0.75, "\u5831\u544a (report)"),
    ("\u4ef2", ""): ("\u9593", 0.80, "\u4ef2\u9593 (companion)"),
    ("\u5192", ""): ("\u967a", 0.85, "\u5192\u967a (adventure)"),
    ("", "\u967a"): ("\u5192", 0.85, "\u5192\u967a (adventure)"),
    ("\u6559", ""): ("\u4f1a", 0.80, "\u6559\u4f1a (church)"),
    ("\u7d39", ""): ("\u4ecb", 0.85, "\u7d39\u4ecb (introduction)"),
    ("", "\u4ecb"): ("\u7d39", 0.80, "\u7d39\u4ecb (introduction)"),
    ("\u8aac", ""): ("\u660e", 0.80, "\u8aac\u660e (explanation)"),
    ("\u5931", ""): ("\u6557", 0.80, "\u5931\u6557 (failure)"),
    ("", "\u6557"): ("\u5931", 0.75, "\u5931\u6557 (failure)"),
    ("\u6210", ""): ("\u529f", 0.75, "\u6210\u529f (success)"),
    ("\u5e0c", ""): ("\u671b", 0.80, "\u5e0c\u671b (hope)"),
    ("\u610f", ""): ("\u5473", 0.75, "\u610f\u5473 (meaning)"),
    ("\u6e96", ""): ("\u5099", 0.75, "\u6e96\u5099 (preparation)"),
    ("\u4ed5", ""): ("\u4e8b", 0.80, "\u4ed5\u4e8b (work)"),
    ("\u6b66", ""): ("\u5668", 0.80, "\u6b66\u5668 (weapon)"),
    ("\u5224", ""): ("\u65ad", 0.75, "\u5224\u65ad (judgment)"),
    ("\u6ce8", ""): ("\u6587", 0.75, "\u6ce8\u6587 (order)"),
    ("\u6848", ""): ("\u5185", 0.75, "\u6848\u5185 (guide)"),
    ("\u7528", ""): ("\u610f", 0.65, "\u7528\u610f (preparation)"),
    ("\u52c7", ""): ("\u6c17", 0.80, "\u52c7\u6c17 (courage)"),
    ("\u60c5", ""): ("\u5831", 0.75, "\u60c5\u5831 (information)"),
    ("\u767b", ""): ("\u5834", 0.65, "\u767b\u5834 (appearance)"),
    ("", "\u671b"): ("\u5e0c", 0.70, "\u5e0c\u671b (hope)"),
    ("\u5230", ""): ("\u7740", 0.75, "\u5230\u7740 (arrival)"),
    ("\u5b89", ""): ("\u5168", 0.70, "\u5b89\u5168 (safety)"),
    ("\u5371", ""): ("\u967a", 0.75, "\u5371\u967a (danger)"),
    ("\u78ba", ""): ("\u8a8d", 0.80, "\u78ba\u8a8d (confirmation)"),
    ("\u6761", ""): ("\u4ef6", 0.80, "\u6761\u4ef6 (condition)"),
    ("\u7d4c", ""): ("\u9a13", 0.75, "\u7d4c\u9a13 (experience)"),
    ("\u88c5", ""): ("\u5099", 0.75, "\u88c5\u5099 (equipment)"),
    ("\u4f9d", ""): ("\u983c", 0.85, "\u4f9d\u983c (request)"),
    ("\u76f8", ""): ("\u624b", 0.70, "\u76f8\u624b (opponent)"),
    ("", "\u65ad"): ("\u5224", 0.65, "\u5224\u65ad (judgment)"),
    ("", "\u5099"): ("\u6e96", 0.65, "\u6e96\u5099 (preparation)"),
    ("", "\u4e8b"): ("\u4ed5", 0.55, "\u4ed5\u4e8b (work)"),
    ("", "\u5185"): ("\u6848", 0.60, "\u6848\u5185 (guide)"),
    ("", "\u8a8d"): ("\u78ba", 0.70, "\u78ba\u8a8d (confirmation)"),
    ("", "\u4ef6"): ("\u6761", 0.65, "\u6761\u4ef6 (condition)"),
    ("", "\u9a13"): ("\u7d4c", 0.60, "\u7d4c\u9a13 (experience)"),
    ("", "\u660e"): ("\u8aac", 0.60, "\u8aac\u660e (explanation)"),
    ("", "\u5668"): ("\u6b66", 0.60, "\u6b66\u5668 (weapon)"),
    ("", "\u6587"): ("\u6ce8", 0.50, "\u6ce8\u6587 (order)"),
    ("", "\u5834"): ("\u767b", 0.40, "\u767b\u5834 (appearance)"),
    ("", "\u624b"): ("\u76f8", 0.45, "\u76f8\u624b (opponent)"),
    ("", "\u4f1a"): ("\u6559", 0.55, "\u6559\u4f1a (church)"),
    ("", "\u9593"): ("\u4ef2", 0.55, "\u4ef2\u9593 (companion)"),
    ("", "\u5168"): ("\u5b89", 0.50, "\u5b89\u5168 (safety)"),
    ("", "\u5473"): ("\u610f", 0.55, "\u610f\u5473 (meaning)"),
    ("", "\u5831"): ("\u60c5", 0.45, "\u60c5\u5831 (information)"),
    ("", "\u610f"): ("\u7528", 0.40, "\u7528\u610f (preparation)"),
    ("", "\u6c17"): ("\u52c7", 0.40, "\u52c7\u6c17 (courage)"),
    ("", "\u7740"): ("\u5230", 0.50, "\u5230\u7740 (arrival)"),
    ("", "\u529f"): ("\u6210", 0.55, "\u6210\u529f (success)"),
}


def load_guide(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.readlines()


def parse_guide_chunks(lines):
    chunks = []
    current_section = ""
    section_pat = re.compile(r"^[A-Z][A-Z\s\d#'\.!]+$")
    speaker_pat = re.compile(r'^(?:\s*)([A-Za-z\s\'\-]+?):\s*["\u201c](.+)', re.DOTALL)
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()
        if stripped and section_pat.match(stripped) and len(stripped) > 5:
            current_section = stripped
            i += 1
            continue
        m = speaker_pat.match(stripped)
        if m:
            speaker = m.group(1).strip()
            text_parts = [m.group(2)]
            j = i + 1
            while j < len(lines):
                nl = lines[j].rstrip()
                ns = nl.strip()
                if not ns:
                    j += 1
                    continue
                if speaker_pat.match(ns):
                    break
                if section_pat.match(ns) and len(ns) > 5:
                    break
                if nl.startswith("\t") or nl.startswith("  "):
                    text_parts.append(ns)
                    j += 1
                else:
                    break
            full_text = " ".join(text_parts).rstrip('"\u201d\u201c')
            chunks.append({
                "line_start": i + 1,
                "line_end": j,
                "speaker": speaker,
                "text": full_text,
                "section": current_section,
            })
            i = j
            continue
        if stripped and len(stripped) > 20:
            chunks.append({
                "line_start": i + 1,
                "line_end": i + 1,
                "speaker": None,
                "text": stripped,
                "section": current_section,
            })
        i += 1
    return chunks


def load_dialogue(path):
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    entries = []
    for item in raw:
        jp = item.get("japanese", "")
        codes = UNMAPPED_PAT.findall(jp)
        mapped = UNMAPPED_PAT.sub("", jp).strip()
        entries.append({
            "resource": item.get("resource", 0),
            "offset": item.get("offset", 0),
            "msg_index": item.get("msg_index", 0),
            "japanese": jp,
            "coverage": item.get("coverage", 0),
            "glyph_count": item.get("glyph_count", 0),
            "unmapped_codes": codes,
            "mapped_text": mapped,
        })
    return entries


def load_glyph_map(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def count_unmapped_frequency(entries):
    counter = Counter()
    for e in entries:
        counter.update(e["unmapped_codes"])
    return counter


def find_name_anchors(jp_text):
    found = {}
    for jp_name, en_name in NAME_MAPPINGS.items():
        if jp_name in jp_text:
            found[jp_name] = en_name
    return found


def score_guide_match(chunk, entry, anchors):
    score = 0.0
    details = []
    gl = chunk["text"].lower()
    for jp_name, en_name in anchors.items():
        if en_name.lower() in gl:
            score += 10.0
            details.append(f"name:{jp_name}={en_name}")
    if chunk["speaker"]:
        sp = chunk["speaker"].lower().strip()
        for jp_name, en_name in NAME_MAPPINGS.items():
            if en_name.lower() == sp and jp_name in entry["japanese"]:
                score += 15.0
                details.append(f"speaker:{en_name}")
    return score, details


def analyze_unmapped_positions(jp_text):
    results = []
    for m in UNMAPPED_PAT.finditer(jp_text):
        code = m.group(1)
        left = UNMAPPED_PAT.sub("", jp_text[:m.start()])[-15:]
        right = UNMAPPED_PAT.sub("", jp_text[m.end():])[:15]
        results.append((code, left, right))
    return results


def gather_all_glyph_contexts(entries, glyph_freq):
    glyph_data = {}
    for code, count in glyph_freq.most_common(100):
        contexts = []
        for entry in entries:
            if f"[{code}]" not in entry["japanese"]:
                continue
            if entry["coverage"] < 60:
                continue
            jp = entry["japanese"]
            for m in UNMAPPED_PAT.finditer(jp):
                if m.group(1) != code:
                    continue
                left = UNMAPPED_PAT.sub("_", jp[:m.start()])[-20:]
                right = UNMAPPED_PAT.sub("_", jp[m.end():])[:20]
                contexts.append({
                    "left": left,
                    "right": right,
                    "resource": entry["resource"],
                    "msg_index": entry["msg_index"],
                    "full_snippet": UNMAPPED_PAT.sub("_", jp)[:80],
                })
            if len(contexts) >= 20:
                break
        glyph_data[code] = {"count": count, "contexts": contexts}
    return glyph_data


def infer_from_compound_patterns(entries, glyph_freq):
    inferences = []
    seen_codes = set()
    for entry in entries:
        if entry["coverage"] < 70:
            continue
        jp = entry["japanese"]
        for m in UNMAPPED_PAT.finditer(jp):
            code = m.group(1)
            if code in seen_codes:
                continue
            start = m.start()
            end = m.end()
            left_text = UNMAPPED_PAT.sub("", jp[:start])
            right_text = UNMAPPED_PAT.sub("", jp[end:])
            lc = left_text[-1] if left_text else ""
            rc = right_text[0] if right_text else ""
            for key in [(lc, rc), (lc, ""), ("", rc)]:
                if key in KNOWN_COMPOUNDS:
                    char, conf, note = KNOWN_COMPOUNDS[key]
                    if key == (lc, "") or key == ("", rc):
                        conf = round(conf * 0.7, 2)
                    inferences.append({
                        "glyph_id": code,
                        "inferred_character": char,
                        "confidence": conf,
                        "evidence_guide_line": 0,
                        "evidence_guide_text": f"Compound: {lc}[{code}]{rc} -> {note}",
                        "evidence_decoded_text": jp[:120],
                        "resource": entry["resource"],
                        "msg_index": entry["msg_index"],
                        "method": "compound_pattern",
                        "occurrences_in_corpus": glyph_freq.get(code, 0),
                    })
                    seen_codes.add(code)
                    break
    return inferences


def infer_from_guide_alignment(entries, guide_chunks, glyph_freq):
    inferences = []
    seen_codes = set()
    high_cov = [e for e in entries
                if e["coverage"] >= 80 and 0 < len(e["unmapped_codes"]) <= 8]
    for entry in high_cov:
        anchors = find_name_anchors(entry["japanese"])
        if not anchors:
            continue
        best_matches = []
        for chunk in guide_chunks:
            score, details = score_guide_match(chunk, entry, anchors)
            if score >= 10:
                best_matches.append((score, chunk, details))
        best_matches.sort(key=lambda x: -x[0])
        if not best_matches:
            continue
        positions = analyze_unmapped_positions(entry["japanese"])
        for code, left_ctx, right_ctx in positions:
            if code in seen_codes:
                continue
            top = best_matches[0]
            inferences.append({
                "glyph_id": code,
                "inferred_character": f"?({left_ctx[-5:]}_{right_ctx[:5]})",
                "confidence": 0.25,
                "evidence_guide_line": top[1]["line_start"],
                "evidence_guide_text": top[1]["text"][:150],
                "evidence_decoded_text": entry["japanese"][:150],
                "resource": entry["resource"],
                "msg_index": entry["msg_index"],
                "method": "guide_alignment",
                "occurrences_in_corpus": glyph_freq.get(code, 0),
            })
            seen_codes.add(code)
    return inferences


def infer_from_frequency_contexts(entries, glyph_freq):
    inferences = []
    glyph_contexts = defaultdict(list)
    for entry in entries:
        if entry["coverage"] < 70:
            continue
        for m in UNMAPPED_PAT.finditer(entry["japanese"]):
            code = m.group(1)
            if glyph_freq[code] < 5:
                continue
            jp = entry["japanese"]
            left = UNMAPPED_PAT.sub("", jp[:m.start()])
            right = UNMAPPED_PAT.sub("", jp[m.end():])
            lc = left[-1] if left else ""
            rc = right[0] if right else ""
            glyph_contexts[code].append({
                "lc": lc, "rc": rc,
                "r": entry["resource"], "i": entry["msg_index"],
            })
    for code, count in glyph_freq.most_common(80):
        if count < 5:
            break
        contexts = glyph_contexts.get(code, [])
        if len(contexts) < 3:
            continue
        pair_counts = Counter()
        for c in contexts:
            pair_counts[(c["lc"], c["rc"])] += 1
        best_pair = pair_counts.most_common(1)
        if not best_pair:
            continue
        (lc, rc), pf = best_pair[0]
        ratio = pf / len(contexts)
        if ratio >= 0.3:
            for key in [(lc, rc), (lc, ""), ("", rc)]:
                if key in KNOWN_COMPOUNDS:
                    char, conf, note = KNOWN_COMPOUNDS[key]
                    adj = round(min(conf, conf * ratio * 2), 2)
                    bc = contexts[0]
                    inferences.append({
                        "glyph_id": code,
                        "inferred_character": char,
                        "confidence": adj,
                        "evidence_guide_line": 0,
                        "evidence_guide_text": (
                            f"Freq={count}, pair {lc}__{rc} "
                            f"({pf}/{len(contexts)}={ratio:.0%}), {note}"
                        ),
                        "evidence_decoded_text": f"R{bc['r']} idx{bc['i']}",
                        "resource": bc["r"],
                        "msg_index": bc["i"],
                        "method": "frequency_compound",
                        "occurrences_in_corpus": count,
                    })
                    break
    return inferences


def detect_mismaps(entries):
    suspicious = {
        "\u9aa8\u5834": ("\u9152\u5834", "tavern"),
        "\u5316\u6ec5": ("\u5546\u5e97", "shop (Vigger)"),
        "\u6bba\u5973": ("\u5c11\u5973 or \u5973\u6027", "girl/woman"),
        "\u5bb6\u5e2f\u65b0": ("\u5e83\u544a\u7d19", "flyer"),
    }
    findings = []
    for current, (likely, reason) in suspicious.items():
        count = 0
        examples = []
        for entry in entries:
            if current in entry["mapped_text"]:
                count += 1
                if len(examples) < 3:
                    examples.append({
                        "resource": entry["resource"],
                        "msg_index": entry["msg_index"],
                        "text": entry["japanese"][:120],
                    })
        if count > 0:
            findings.append({
                "current_reading": current,
                "likely_correct": likely,
                "reason": reason,
                "occurrences": count,
                "examples": examples,
            })
    return findings


def deduplicate(inferences):
    best = {}
    for inf in inferences:
        code = inf["glyph_id"]
        if code not in best or inf["confidence"] > best[code]["confidence"]:
            best[code] = inf
        elif (inf["confidence"] == best[code]["confidence"]
              and inf["occurrences_in_corpus"] > best[code]["occurrences_in_corpus"]):
            best[code] = inf
    return sorted(
        best.values(),
        key=lambda x: (-x["confidence"], -x["occurrences_in_corpus"])
    )


def main():
    print("=" * 70)
    print("GUIDE CROSS-REFERENCE TOOL")
    print("Inferring unmapped glyphs from English guide alignment")
    print("=" * 70)

    print("\n[1/5] Loading data...")
    guide_lines = load_guide(GUIDE_PATH)
    print(f"  Guide: {len(guide_lines)} lines")
    entries = load_dialogue(DIALOGUE_PATH)
    print(f"  Dialogue: {len(entries)} entries")
    glyph_map = load_glyph_map(GLYPH_MAP_PATH)
    print(f"  Glyph map: {len(glyph_map)} entries")

    print("\n[2/5] Analyzing unmapped glyph frequency...")
    glyph_freq = count_unmapped_frequency(entries)
    total_unmapped = sum(glyph_freq.values())
    unique_unmapped = len(glyph_freq)
    print(f"  Total unmapped glyph occurrences: {total_unmapped}")
    print(f"  Unique unmapped glyph codes: {unique_unmapped}")
    print(f"\n  Top 30 most frequent unmapped glyphs:")
    for code, count in glyph_freq.most_common(30):
        print(f"    [{code}] = {count} occurrences")

    print("\n[3/5] Parsing guide into dialogue chunks...")
    guide_chunks = parse_guide_chunks(guide_lines)
    print(f"  Parsed {len(guide_chunks)} guide chunks")
    speakers = Counter(c["speaker"] for c in guide_chunks if c["speaker"])
    print(f"  Top speakers: {speakers.most_common(10)}")

    print("\n[4/5] Running inference strategies...")
    all_inferences = []

    print("\n  --- Strategy A: Compound Pattern Matching ---")
    compound_infs = infer_from_compound_patterns(entries, glyph_freq)
    print(f"  Found {len(compound_infs)} compound pattern inferences")
    all_inferences.extend(compound_infs)

    print("\n  --- Strategy B: Guide Alignment ---")
    guide_infs = infer_from_guide_alignment(entries, guide_chunks, glyph_freq)
    print(f"  Found {len(guide_infs)} guide alignment inferences")
    all_inferences.extend(guide_infs)

    print("\n  --- Strategy C: Frequency-Context Analysis ---")
    freq_infs = infer_from_frequency_contexts(entries, glyph_freq)
    print(f"  Found {len(freq_infs)} frequency-context inferences")
    all_inferences.extend(freq_infs)

    best_inferences = deduplicate(all_inferences)
    print(f"\n  {len(best_inferences)} unique glyph inferences after dedup")

    print("\n  --- Mismap Detection ---")
    mismaps = detect_mismaps(entries)
    for mm in mismaps:
        print(f"    '{mm['current_reading']}' -> likely "
              f"'{mm['likely_correct']}' ({mm['occurrences']}x) - {mm['reason']}")

    print("\n[5/5] Gathering comprehensive glyph contexts...")
    glyph_contexts = gather_all_glyph_contexts(entries, glyph_freq)

    output = {
        "summary": {
            "total_entries": len(entries),
            "total_unmapped_occurrences": total_unmapped,
            "unique_unmapped_codes": unique_unmapped,
            "inferences_found": len(best_inferences),
            "guide_chunks_parsed": len(guide_chunks),
        },
        "top_unmapped_glyphs": [
            {"code": code, "occurrences": count}
            for code, count in glyph_freq.most_common(50)
        ],
        "inferences": best_inferences,
        "likely_mismappings": mismaps,
        "glyph_contexts": {
            code: {
                "occurrences": data["count"],
                "sample_contexts": data["contexts"][:10],
            }
            for code, data in glyph_contexts.items()
        },
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\nOutput written to: {OUTPUT_PATH}")

    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)

    high_conf = [i for i in best_inferences if i["confidence"] >= 0.7]
    med_conf = [i for i in best_inferences if 0.4 <= i["confidence"] < 0.7]
    low_conf = [i for i in best_inferences if i["confidence"] < 0.4]

    print(f"\nHigh confidence (>=0.7): {len(high_conf)} inferences")
    for inf in sorted(high_conf, key=lambda x: -x["occurrences_in_corpus"])[:20]:
        print(f"  [{inf['glyph_id']}] -> '{inf['inferred_character']}' "
              f"(conf={inf['confidence']:.2f}, "
              f"{inf['occurrences_in_corpus']} occ, "
              f"method={inf['method']})")
        print(f"    Evidence: {inf['evidence_guide_text'][:80]}")

    print(f"\nMedium confidence (0.4-0.7): {len(med_conf)} inferences")
    for inf in sorted(med_conf, key=lambda x: -x["occurrences_in_corpus"])[:15]:
        print(f"  [{inf['glyph_id']}] -> '{inf['inferred_character']}' "
              f"(conf={inf['confidence']:.2f}, "
              f"{inf['occurrences_in_corpus']} occ)")

    print(f"\nLow confidence (<0.4): {len(low_conf)} inferences")

    print(f"\nLikely mismappings: {len(mismaps)}")
    for mm in mismaps:
        print(f"  '{mm['current_reading']}' x{mm['occurrences']} "
              f"-> likely '{mm['likely_correct']}' ({mm['reason']})")

    print(f"\nTop 20 unmapped glyphs by frequency:")
    for code, count in glyph_freq.most_common(20):
        resolved = any(
            i["glyph_id"] == code and i["confidence"] >= 0.5
            for i in best_inferences
        )
        tag = "INFERRED" if resolved else "UNRESOLVED"
        char = ""
        for i in best_inferences:
            if i["glyph_id"] == code:
                char = (f" -> '{i['inferred_character']}' "
                        f"({i['confidence']:.2f})")
                break
        print(f"  [{code}] {count:>5} occ - {tag}{char}")


if __name__ == "__main__":
    main()
