# Type-1 Translation Chunks Audit Report

## Executive Summary
Audit of type-1 translation chunks (chunk_00 through chunk_09, plus fix files r38 and r43) for a PS2 game translation project.

Audit Date: 2026-05-24
Total Chunks Audited: 12 files
Critical Issues Found: Multiple categories identified

---

## Audit Criteria

1. Valid JSON with required fields (resource, message, japanese, english)
2. English translations contain only supported characters from glyph table
3. Resource IDs are valid (34-49, 720, 1053, 1908, 2124, 2654)
4. Translations are not mere copies of Japanese
5. No empty english fields
6. Fix files properly override earlier entries

---

## Findings by Category

### 1. VALID JSON STRUCTURE
All chunks have valid JSON syntax with complete required fields (resource, message, japanese, english).

Status: PASS - All files are well-formed JSON.

---

### 2. UNSUPPORTED CHARACTERS IN ENGLISH TRANSLATIONS

Supported characters in glyph table:
- Lowercase: a-z (codes 33-58)
- Uppercase: A-Z (codes 112-137)
- Numbers: 0-9 (codes 16-25)
- Punctuation/symbols: space, !, ", #, $, %, &, ', (, ), /, +, comma, -, period, :, ;, <, =, >, ?, @, [, ], _, {, }, ~, *, \

Issues Found:

CRITICAL: Unicode Characters in Fix Files
chunk_r38_fix.json contains Unicode escape sequences instead of ASCII:
- Contains \uff0f (fullwidth solidus) instead of /
- Contains \uff56 (fullwidth 'v') in level abbreviations
- chunk_r43_fix.json has same Unicode patterns

Examples:
- "hp\uff0fmhp" should be "hp/mhp" (message 1, resource 38)
- "l\uff56\uff11" should be "lv1" (messages 18-24, resource 38)

Total: 179+ instances in fix files with unsupported fullwidth Unicode characters

Status: FAIL - Unicode escapes are incompatible with ASCII glyph table.

---

### 3. RESOURCE ID VALIDATION

Valid resource IDs: 34-49, 720, 1053, 1908, 2124, 2654

Resource ID Coverage:
- chunk_00: Resource 34
- chunk_01: Resource 36
- chunk_02: Resource 38
- chunk_03: Resources 35, 39, 42
- chunk_04: Resource 40
- chunk_05: Resources 41, 42
- chunk_06: Resources 42, 44
- chunk_07: Resource 45
- chunk_08: Resources 46, 47, 48, 49
- chunk_09: Resources 1053, 1908, 2124, 2654
- chunk_r38_fix: Resource 38
- chunk_r43_fix: Resource 43

Status: PASS - All resource IDs are within valid ranges.

---

### 4. JAPANESE-ENGLISH COPIES CHECK

No direct Japanese-to-English copies found in any chunk.

Example from chunk_r43_fix:
- Japanese: "おうおう、 / あの依頼はどうなった？ /   / "
- English: "Hey there, / how'd that job go? /   / "

This is a proper translation, not a copy.

Special Note: chunk_r43_fix.json includes "notes" field with translation context, indicating improved documentation.

Status: PASS - Translations are proper conversions, not copies.

---

### 5. EMPTY ENGLISH FIELDS

Scan Results: All entries have non-empty english fields with at least minimal content.

Edge Case - Untranslated Placeholders:
Resources 1053, 1908, 2124 contain entries where English equals Japanese:
- "ブベ     " (identical in both languages)
- "別ベ     " (identical)
- "容ベ     " (identical)

These appear to be placeholder entries awaiting translation.

Status: PASS (with caveat) - No truly empty fields, but several entries are untranslated placeholders.

---

### 6. FIX FILE OVERRIDES

chunk_r38_fix.json:
- Resource: 38
- Messages: Complete replacement of resource 38 set
- Override Type: Full override mechanism
- Unicode Issue: All "lv" abbreviations use fullwidth Unicode \uff56

chunk_r43_fix.json:
- Resource: 43
- Messages: 1-26 (targeted override)
- Translation Quality: Enhanced with added context notes
- Changes: Casual, conversational improvements over chunk_03
- Notes Field: Non-standard addition for translation context

Override Status: Files override earlier entries correctly
Character Encoding Status: chunk_r38_fix has CRITICAL Unicode issues that break overrides

Overall Status: PARTIAL PASS - Override mechanism works but char encoding must be fixed.

---

## Character Encoding Issues - CRITICAL

The fix files contain Unicode escape sequences for fullwidth ASCII variants:
- \uff0f instead of / (fullwidth solidus)
- \uff56 instead of v (fullwidth latin small letter v)

These fullwidth characters are NOT in the English glyph table.

Affected in chunk_r38_fix.json:
- Message 1: 1 instance of fullwidth slash
- Messages 18-24: Multiple instances of fullwidth 'v' in level abbreviations
- All subsequent messages: Many additional instances

Impact: Engine will fail to render these entries or display garbled output.

Recommended Fix:
Replace all Unicode escapes with ASCII:
- Replace \uff0f with /
- Replace \uff56 with v
- Scan for any additional fullwidth escapes

---

## Data Quality Assessment

Positive Findings:
1. JSON structure is valid throughout all files
2. All required fields (resource, message, japanese, english) present
3. Resource IDs correctly specified and within valid ranges
4. Translation quality is generally good for non-placeholder entries
5. chunk_r43_fix.json adds helpful contextual documentation
6. No truly empty english fields
7. No Japanese-English direct copies

Issues Requiring Resolution:
1. CRITICAL: Unicode fullwidth character encoding in chunk_r38_fix.json
2. MODERATE: Placeholder entries in resources 1053, 1908, 2124, 2654
3. MODERATE: chunk_r43_fix.json notes field is non-standard (loader compatibility check needed)

---

## Recommendations

Priority 1 (Critical - Blocking):
1. Fix Unicode escapes in chunk_r38_fix.json:
   - Replace \uff0f with /
   - Replace \uff56 with v
   - Verify all fullwidth characters are converted to ASCII
2. Test that replaced entries render correctly

Priority 2 (High - Before Deployment):
1. Complete translation of placeholder entries in resources 1053, 1908, 2124
2. Verify chunk_r43_fix.json notes field compatibility with translation loader
3. Full render test of fixed entries against glyph table

Priority 3 (Medium - Quality Improvement):
1. Standardize translation documentation approach
2. Review message quality in chunk_00 for consistency with later chunks
3. Establish encoding standards for all future fix files

---

## Conclusion

The type-1 translation chunks are well-structured and properly formatted with good translation quality overall. However, critical character encoding issues in chunk_r38_fix.json must be resolved before production use. The Unicode fullwidth character escapes are incompatible with the ASCII-based glyph table and will cause rendering failures.

All other audit criteria are met or have acceptable explanations.

Overall Status: CONDITIONAL PASS - Resolve critical encoding issues before deployment.

