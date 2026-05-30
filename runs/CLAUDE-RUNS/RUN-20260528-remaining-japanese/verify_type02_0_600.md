# Type-02 Resource Verification: R0-R600

**Date:** 2026-05-28
**Range:** R0 through R600
**Goal:** Identify untranslated type-02 resources containing Japanese dialogue

## Summary

- **Total type-02 resources in R0-R600:** 78
- **Already translated:** 2 (R35, R39)
- **Untranslated with text (FFFE > 0):** 0
- **Untranslated binary-only:** 76
- **New dialogue found:** NONE

## FFFE Scan Results

Of 76 untranslated type-02 resources, 73 had zero FFFE bytes (clearly binary).

Three resources (R29, R30, R31) contained FFFE byte sequences, but further analysis confirmed these are **NOT text**:

| RID | FFFE count | Size (bytes) | Glyph hit % | Verdict |
|-----|-----------|-------------|-------------|---------|
| R29 | 1 | 6,580 | 0.1% | Binary (3D geometry/float data) |
| R30 | 15 | 16,644 | 0.2% | Binary (3D geometry/float data) |
| R31 | 1 | 9,076 | 0.0% | Binary (3D geometry/float data) |

**Evidence:** The FFFE bytes in R29/R30/R31 appear within IEEE 754 floating-point sequences (surrounded by values like `00 00 80 3F` = float 1.0). For example, `FE FF 9F C0` decodes to the float `-5.0`. No contiguous runs of valid glyph indices were found (max run length = 1 vs. expected 5+ for real text).

## Full Resource List

### Binary (no text, FFFE = 0) -- 73 resources
R27, R28, R32, R51, R134, R136, R145, R151, R155, R156, R165, R167, R183, R231, R240, R241, R245, R307, R308, R311, R314, R315, R319, R322, R325, R326, R332, R333, R338, R342, R393, R402, R403, R408, R412, R413, R415, R416, R420, R422, R427, R428, R434, R435, R439, R442, R443, R444, R445, R447, R449, R453, R457, R465, R467, R471, R473, R474, R500, R502, R503, R507, R508, R509, R512, R514, R515, R530, R531, R558, R584, R588, R599, R600

### False-positive FFFE (float data, not text) -- 3 resources
R29, R30, R31

### Already translated -- 2 resources
R35, R39

## Conclusion

**No batch_verify_0_600.json needed.** All untranslated type-02 resources in the R0-R600 range are binary data (3D geometry, configuration, etc.) with no Japanese dialogue to translate.
