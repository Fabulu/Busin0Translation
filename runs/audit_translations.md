# Translation Data Integrity Audit Report

## Executive Summary

- **Total entries analyzed**: 12887
- **Total entries with issues**: 6563
- **Pass rate**: 49.1%

## Critical Findings

- **batch_01.json**: 1602 entries with Japanese text
- **batch_02.json**: 4 extremely long translations
- **batch_03.json**: 1 extremely long translations
- **batch_04.json**: 3 extremely long translations, 833 entries with Japanese text
- **batch_06.json**: 3 extremely long translations, 832 entries with Japanese text
- **batch_07.json**: 2 extremely long translations

## Detailed Results by Batch

### batch_01.json
- **Total entries**: 1989
- **Issues found**: 3220
  - Invalid characters: 1618
  - Untranslated Japanese: 1602

### batch_02.json
- **Total entries**: 936
- **Issues found**: 4
  - Long translations: 4

### batch_03.json
- **Total entries**: 1580
- **Issues found**: 1
  - Long translations: 1

### batch_04.json
- **Total entries**: 1833
- **Issues found**: 1669
  - Invalid characters: 833
  - Long translations: 3
  - Untranslated Japanese: 833

### batch_05.json
- **Total entries**: 1761
- **Status**: PASS

### batch_06.json
- **Total entries**: 1484
- **Issues found**: 1667
  - Invalid characters: 832
  - Long translations: 3
  - Untranslated Japanese: 832

### batch_07.json
- **Total entries**: 1368
- **Issues found**: 2
  - Long translations: 2

### batch_08.json
- **Total entries**: 750
- **Status**: PASS

### batch_09.json
- **Total entries**: 935
- **Status**: PASS

### batch_10.json
- **Total entries**: 137
- **Status**: PASS

### batch_11.json
- **Total entries**: 114
- **Status**: PASS

## Findings by Category

### 1. Required Fields (resource, msg_index, japanese, english)
**Result**: PASS

### 2. Duplicate (resource, msg_index) Pairs
**Result**: PASS

### 3. Character Set Validation
Supported: a-z, A-Z, 0-9, space, ! " # $ % & ' ( ) + , - . / : ; < = > ? @ [ ] _ { } ~ *
**Result**: 3283 entries with unsupported characters

### 4. Translation Length (max 200 chars)
**Result**: 13 entries exceed limit
  - batch_02.json: 4 entries
  - batch_03.json: 1 entries
  - batch_04.json: 3 entries
  - batch_06.json: 3 entries
  - batch_07.json: 2 entries

### 5. Untranslated Japanese Text
**Result**: 3267 entries contain Japanese
  - batch_01.json: 1602 entries (80.5%)
  - batch_04.json: 833 entries (45.4%)
  - batch_06.json: 832 entries (56.1%)

## Recommendations

1. **CRITICAL**: Translate 3267 entries containing Japanese text

2. **HIGH**: Reduce 13 translations exceeding 200 characters

3. **MEDIUM**: Fix 3283 entries with unsupported characters

## Technical Details
- Analysis: 2026-05-24
- Total entries: 12887
- Issues found: 6563
- Glyph table: data/english_glyph_table.json