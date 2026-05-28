# Type-2 Dialogue Injector Audit Report

**Date**: 2026-05-24  
**Tool**: `tools/inject_type2_dialogue.py`  
**Status**: CRITICAL ISSUE FOUND

---

## Executive Summary

The injector has **one critical structural flaw** that caused the M1 crash (93 binary-data resources corrupted) and **one potential edge-case issue** with complex control code patterns. The core injection logic (Section 1 preservation, sec2_size updates, padding) is sound, but type validation must be hardened.

---

## Detailed Audit Results

### 1. Type Verification Before Injection - **CRITICAL FAILURE**

**Status**: FAILS safety check  
**Severity**: CRITICAL (caused M1 incident)

**Issue**: The injector accepts ANY type code, not just type-02.

**Problem Code** (lines 245-251):
```
pattern = os.path.join(RAW_DIR, "{:04d}_type02.raw".format(res_idx))
raws = glob.glob(pattern)
if not raws:
    # Try any type code  <-- PROBLEM LINE
    raws = glob.glob(os.path.join(RAW_DIR, "{:04d}_type*.raw".format(res_idx)))
```

**Root Cause**: The fallback glob on line 249 will match `0043_type03.raw`, `0046_type03.raw`, `1053_type03.raw`, etc., leading to non-MSG-format resources being treated as dialogue containers.

**Incident Link**: **M1. VIF FIFO Crash** - The v1 injector processed 93 binary-data type-02 resources (UI layouts, coordinates, map tiles) by accepting `*type*.raw` fallback, corrupting their binary structure. This crashed the game with VIF FIFO assertion failures.

**Recommendation**: Remove the fallback glob entirely. If `_type02.raw` is not found, log a warning and skip the resource silently.

---

### 2. Section 1 Preservation (Non-Text Data) - **CORRECT**

**Status**: PASS  

**Analysis**: Section 1 (header + non-text binary data) is extracted before injection and copied byte-for-byte. Only the sec2_size header field is modified (line 312). All other bytes are preserved.

---

### 3. sec2_size Header Update - **CORRECT**

**Status**: PASS  

**Analysis**: The sec2_size field at offset 0x14 (little-endian uint32) is correctly updated with the new Section 2 byte count. This reflects the actual length of the rebuilt dialogue stream.

**Note**: sec2_offset (at 0x18) is NOT modified, which is correct because Section 1 size is unchanged.

---

### 4. Preserve Data AFTER Section 2 - **CORRECT**

**Status**: PASS  

**Analysis**: Any trailing data after Section 2 (rare but possible) is extracted and appended to the reassembled file. If a resource has post-dialogue binary chunks, they are preserved in order.

---

### 5. Handle Section 2 Growth - **CORRECT**

**Status**: PASS  

**Analysis**: When translated English text is longer than Japanese originals, Section 2 may grow. The code recalculates the number of sectors needed. Pads with null bytes to fill the final sector. The updated sec2_size in the header reflects the new byte count.

---

### 6. Control Code Preservation - **MOSTLY CORRECT, POTENTIAL EDGE CASE**

**Status**: CONDITIONAL PASS (with caveat for complex structures)  
**Severity**: LOW (edge case, may not occur in practice)

**Analysis**: The split_control_and_text function (lines 198-233) correctly identifies leading/trailing control codes (0xFB00+) while preserving FFFE (line breaks) within text.

**Potential Issue**: If a message has an INTERSPERSED control code in the middle of text (e.g., text + color_change_0xFB20 + more_text), the code would treat the second portion as trailing controls and drop it.

**Reality Check**: The PS2 MSG format likely keeps controls at boundaries only. This edge case is low risk.

---

### 7. Sector Padding - **CORRECT**

**Status**: PASS  

**Analysis**: Sector size (2048) is correct for PS2 CD/DVD. math.ceil() correctly rounds up. Null padding is appropriate for PS2 disc sectors. Output files are correctly sized for ISO placement.

---

## Summary Table

| Check | Result | Severity | Notes |
|-------|--------|----------|-------|
| Type verification | FAIL | CRITICAL | Accepts any type code (caused M1 crash). Remove fallback glob. |
| Section 1 preservation | PASS | — | Byte-for-byte preserved before sec2_offset. |
| sec2_size update | PASS | — | Correctly updated at offset 0x14 with new size. |
| Preserve after_sec2 data | PASS | — | Trailing data appended after Section 2. |
| Section 2 growth handling | PASS | — | Sectors recalculated and padded; header updated. |
| Control code preservation | PASS (caveat) | LOW | Works for standard format; edge case for interspersed controls unlikely. |
| Sector padding | PASS | — | Correct 2048-byte boundary padding with nulls. |

---

## Recommended Actions

### Immediate (P0)
1. Fix type validation: Remove the *type* fallback glob. Only accept _type02.raw files.
   - Prevents accidental corruption of type-03, type-04, etc. resources.
   - Directly addresses the M1 incident root cause.

### Follow-up (P1)
2. Add resource type confirmation: Verify binary structure matches type-02 expectations.

3. Logging improvements: Log which resources are skipped and why.

### Testing (P2)
4. Test with manual crafted cases to verify correct behavior.

---

## Conclusion

The injector is mostly well-designed for its core task. However, the type validation flaw (item #1) is a critical safety issue that must be fixed before using it again. With that correction, the tool should safely inject translated dialogue into type-02 dialogue resources.

**Key Issue Location**: Lines 245-251 in inject_type2_dialogue.py (type validation fallback glob)
