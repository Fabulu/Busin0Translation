# VRAM Edit Check: R1188 Stat Labels in 27-5 Save State

## Summary

**The R1188 stat label edits are NOT in the 27-5 save state's VRAM because the save state was created from an ISO build that did not include them.**

## Evidence

### Save state timing vs ISO builds

| Artifact | Timestamp |
|----------|-----------|
| 27-5.p2s save state | 2026-05-31 21:08:40 |
| BUSIN0_EN_v27.iso | 2026-05-31 20:00 |
| BUSIN0_EN_v28.iso | 2026-05-31 21:39 |
| BUSIN0_EN_v29.iso | 2026-05-31 22:48 |

The save state was created at 21:08, after v27 (20:00) but before v28 (21:39).
The game was running from v27 or possibly v26.

### R1188 content in each ISO

| ISO | Matches original | Matches patched (stat labels) | Status |
|-----|-----------------|-------------------------------|--------|
| v26 | 527,316/528,384 (99.8%) | 510,864/528,384 (96.7%) | Direct patches only |
| v27 | 527,316/528,384 (99.8%) | 510,864/528,384 (96.7%) | Direct patches only |
| v28 | 527,316/528,384 (99.8%) | 510,864/528,384 (96.7%) | Direct patches only |
| **v29** | - | **528,384/528,384 (100%)** | **Full stat label patches** |
| **v30** | - | **528,384/528,384 (100%)** | **Full stat label patches** |

### What the save state shows

The screenshot from 27-5.p2s confirms:
- Japanese stat labels visible: 力, 知恵, 信仰心, 生命力, 敏捷度, 幸運度
- English text working: "Class&Parameter", "Fighter", "Mage", "Priest", "Bonus Point", etc.
- The `patch_r1188_direct.py` name-entry tab changes (1,068 byte diffs) were present
- The `patch_r1188_stats.py` stat label changes (16,884 byte diffs) were NOT present

### Pixel data breakdown

- `patch_r1188_direct.py`: Changes 1,068 pixel bytes (name entry labels). Present in v26-v30.
- `patch_r1188_stats.py`: Changes 16,884 pixel bytes (stat labels). First appears in v29.
- Combined total diffs vs original: 17,520 bytes.

## Conclusion

**This is NOT a VRAM coordinate mapping problem or a game rejection issue.**
The stat label patches simply were not included in the ISO that generated this save state.

The stat labels were first patched into the build starting with v29.
To verify the stat labels work, a new save state must be taken from v29 or later (or v30 = latest).

## Next Steps

1. Load v29 or v30 ISO in PCSX2
2. Navigate to the character creation / stat screen
3. Take a new save state
4. Verify that stat labels show English letters (T, IQ, PIE, VIT, AGI, LCI)
