# ISO Debug: Hash Comparison Report
Generated: 2026-05-28

## CRITICAL FINDING: v9, v13, v14, v15 are IDENTICAL files

The build script (`build/build_v9.py`) is hardcoded to output `BUSIN0_EN_v9.iso`.
Versions v13/v14/v15 are just copies of v9 -- they have the same MD5 hash.

## MD5 Hashes (all ISOs, same file size: 1,274,544,128 bytes)

| File | MD5 | Notes |
|------|-----|-------|
| Original JP ISO | `48a5639afdf9931913c7dde298dc5349` | Baseline |
| BUSIN0_EN.iso | `44d2169f57a7fa33d42e1994b769de5d` | Early build |
| v3 | `163e591514a77eb107f970c91c35c535` | Unique |
| v4 | `afa32f8fa27aa66d1d82ca65bcacbebe` | Unique |
| v5 | `52e87dfde367cfbe4a6fdef3ae648269` | Unique |
| v6 | `4c6b4d5cfd584c4049f04b49e8d83f17` | Same as v8 |
| v7 | `4a022f9161fd604d2933da07121c36ae` | Unique |
| v8 | `4c6b4d5cfd584c4049f04b49e8d83f17` | Same as v6 |
| **v9** | **`ec0fe98b45c740dcd81f231e232cc668`** | **= v13 = v14 = v15** |
| v10 | `2f421343618eba40afc7dee301d902f0` | Unique |
| v11 | `3d6b77386e7e82b7d1b528a11a27eda1` | Unique |
| **v13** | **`ec0fe98b45c740dcd81f231e232cc668`** | **= v9** |
| **v14** | **`ec0fe98b45c740dcd81f231e232cc668`** | **= v9** |
| **v15** | **`ec0fe98b45c740dcd81f231e232cc668`** | **= v9** |

## Root Cause Analysis

### 1. Build script always writes v9
`build/build_v9.py` line 262-263:
```python
shutil.copy2('Busin 0 - ...iso', 'build/BUSIN0_EN_v9.iso')
with open('build/BUSIN0_EN_v9.iso', 'r+b') as iso:
```
The output filename is hardcoded. Running the script always overwrites v9.

### 2. PACKDATA_v3.DIG is stale
The intermediate PACKDATA file hasn't been regenerated:
- `build/PACKDATA_v3.DIG` -- last modified **May 28 20:39** (MD5: `01d95d611ec0a5a9cfd907afb6003598`)
- Even if the build script runs, it reads this same stale file and writes the same data.

### 3. v13/v14/v15 are manual copies
Timestamps and identical hashes confirm v13/v14/v15 are just copies of v9.
- v9: May 30 15:14 (overwritten to match v15's timestamp)
- v13: May 30 10:20
- v14: May 30 10:28
- v15: May 30 15:14

## PACKDATA Sizes (confirms v15 IS patched vs JP original)

| ISO | PACKDATA size | EXE size |
|-----|--------------|----------|
| Original JP | 839,661,568 | 4,185,776 |
| v15 (=v9) | 839,843,840 | 4,185,776 |

The PACKDATA in v15 is 182,272 bytes larger than JP original, confirming English text injection IS present -- but it's the same injection from the v9 build era.

## What Must Change for a Real v16

1. **Regenerate `build/PACKDATA_v3.DIG`** from updated `build/packdata_resources/` via `build/rebuild_packdata.py`
2. **Update the build script output filename** or add a version parameter
3. **Verify the rebuilt ISO has a new MD5 hash** different from `ec0fe98b45c740dcd81f231e232cc668`
