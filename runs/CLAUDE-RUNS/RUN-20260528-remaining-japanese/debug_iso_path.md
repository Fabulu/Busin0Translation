# Debug: ISO Path Verification for build_v9.py Step 8

Date: 2026-05-28

## Findings

### Q1: What ISO does Step 8 copy as the base?

Line 262: `shutil.copy2('Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso', 'build/BUSIN0_EN_v9.iso')`

**Source: the ORIGINAL Japanese ISO** -- not a previously built one. This is correct.

### Q2: What filename does it write?

Always writes to `build/BUSIN0_EN_v9.iso`. The build script hardcodes "v9" in the output filename.

### Q3: Is v15 just a copy of v9?

**YES.** MD5 checksums are identical:
- v9:  `ec0fe98b45c740dcd81f231e232cc668`
- v15: `ec0fe98b45c740dcd81f231e232cc668`

Both files are 1,274,544,128 bytes, last modified at the same time (May 30 15:14).
v15 is a byte-for-byte copy of v9. No script in `build/*.py` references "v15" -- it was likely created by a manual file copy.

### Q4: Does the ISO patching actually overwrite the PACKDATA region?

**YES, verified correct.**

| Property | Original ISO | Patched ISO (v9) |
|---|---|---|
| PACKDATA LBA | 16029 | 16029 (unchanged) |
| PACKDATA size in dir entry | 839,661,568 (800.8 MB) | 839,843,840 (800.9 MB) |
| PACKDATA_v3.DIG file size | -- | 839,843,840 |
| Dir entry size matches file | -- | YES |
| Size LE == Size BE | -- | YES |
| Fits in available space | -- | YES (1,184 MB available) |

The patched PACKDATA is ~182 KB larger than the original. This fits comfortably -- there is 1,184 MB of space from the PACKDATA LBA to the end of the ISO.

The directory entry's size field (both little-endian and big-endian copies) is correctly updated to match the actual PACKDATA_v3.DIG file size.

### Q5: Risk of stale v15

If the user:
1. Runs build_v9.py (writes to v9)
2. Copies v9 to v15
3. Later re-runs build_v9.py (overwrites v9 with new content)
4. Tests v15 (still the OLD build)

...then v15 would be stale. Currently they are identical, so this is not an active problem, but the manual copy workflow is fragile.

## Conclusion

**No issues found.** Step 8 correctly:
- Starts from the original Japanese ISO (clean base each time)
- Overwrites PACKDATA.DIG at the correct LBA with the rebuilt file
- Updates the ISO 9660 directory entry size (both LE and BE)
- Patches the EXE at the correct LBA (Step 8.5)

v15 is an exact copy of v9 and not stale.
