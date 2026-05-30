# Type-02 Resource Verification: R750-R1000

## Summary

**Range scanned:** R0750 - R1000
**Total type-02 resources:** 143
**Already translated:** 35 (all marked as [DATA], [LAYOUT], or [SYSTEM])
**Untranslated remaining:** 108

**Verdict: NO REAL DIALOGUE FOUND. No batch file created.**

## Methodology

1. Identified 143 type-02 resources in R750-R1000 from manifest.json
2. Excluded 35 already-translated IDs (from batch_10.json and batch_gap989.json)
3. Scanned all 108 untranslated .raw files for FFFE (0xFE 0xFF) line-break markers
4. For resources with FFFE > 0: decoded surrounding context using msg_glyph_map.json
5. Computed glyph-match percentage (% of 16-bit words near FFFE that resolve to known glyphs)
6. Cross-referenced against already-translated resources in this range for baseline

## Key Findings

### Already-translated resources are ALL data/layout (not dialogue)

Every translated resource in batch_10.json (R750-R1000 range) was tagged as:
- `[DATA]` - binary/coordinate data
- `[LAYOUT]` - menu template / grid positions
- `[SYSTEM]` - system labels, menu indices
- `[GLYPH TEST]` - glyph rendering test strings

Zero entries contained actual narrative dialogue or NPC conversations.

### FFFE markers are false positives from binary data

- 87 of 108 untranslated resources contain FFFE byte pairs
- Glyph-match analysis: highest match rate was 31.5% (R0771, R0815, R0819)
- Even known-translated resources in this range scored similarly (R0757 = 22.2%, R0769 = 16.5%)
- Decoded context around FFFE markers shows scattered, incoherent character fragments
- These are coincidental 0xFFFE values in 3D geometry, texture, and scene data

### Resource structure confirms scene/dungeon containers

All resources share the same binary container header (offset table at 0x00, sub-section pointers). These are dungeon floor / scene packages containing:
- 3D model geometry
- Texture data
- Lighting/camera parameters
- Occasionally small embedded MSG blocks with UI layout coordinates (not dialogue)

## Breakdown by FFFE Count

### With FFFE (87 resources) - ALL BINARY/SCENE DATA
| FFFE Count | Resources |
|-----------|-----------|
| 100+ | R0753, R0755, R0773, R0777, R0781, R0783, R0805, R0807, R0809, R0811, R0821, R0823, R0825, R0855, R0857, R0869, R0887, R0897, R0902, R0910, R0912, R0914, R0916, R0918 |
| 30-99 | R0752, R0756, R0759, R0761, R0763, R0765, R0767, R0773, R0781, R0783, R0806, R0808, R0810, R0812, R0813, R0817, R0820, R0827, R0829, R0841, R0843, R0845, R0906, R0915 |
| 1-29 | R0751, R0762, R0766, R0770, R0771, R0772, R0775, R0779, R0782, R0788, R0800, R0802, R0814, R0815, R0818, R0819, R0831, R0833, R0835, R0836, R0842, R0847, R0849, R0851, R0853, R0854, R0856, R0859, R0861, R0863, R0865, R0867, R0888, R0898, R0903, R0907, R0908, R0913, R0923, R0924, R0925, R0930 |

### Without FFFE (21 resources) - CONFIRMED BINARY
R0754, R0760, R0768, R0774, R0776, R0778, R0804, R0822, R0824, R0826, R0832, R0834, R0846, R0858, R0890, R0909, R0911, R0922, R0926, R0928, R0931

## Conclusion

The R750-R1000 range consists entirely of scene/dungeon container resources. No translatable dialogue exists in the untranslated resources. This is consistent with the game's data layout where dialogue resources are concentrated in other index ranges (R35-R48 for menus, R680-R750 for dungeon events, R1100+ for story scenes).
