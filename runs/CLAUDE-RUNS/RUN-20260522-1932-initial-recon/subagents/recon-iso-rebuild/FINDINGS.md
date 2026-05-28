# ISO Rebuild and xdelta Patch Research Findings

## Status: RESEARCH COMPLETE (tool verification pending)

NOTE: Bash access was intermittently denied during this research session.
The answers below marked [NEEDS VERIFICATION] require running the indicated
commands to confirm. All other answers are based on web research and the
existing ARCHITECTURE_PLAN.md.

---

## 1. Is pycdlib installed?

**[NEEDS VERIFICATION]** Run: `pip show pycdlib`

If not installed, install with: `pip install pycdlib`

pycdlib is a pure-Python library (no C dependencies), so it installs
trivially on Windows. Current version on PyPI is 1.14.0+.

---

## 2. Is xdelta3 available on this Windows system?

**[NEEDS VERIFICATION]** Run: `xdelta3 --version` or `where xdelta3`

If not available, options:
- Download xdelta3.exe from https://github.com/jmacd/xdelta-gpl/releases
  or from romhacking.net
- Place `xdelta3.exe` in the project directory or add to PATH
- Alternative GUI tools: Delta Patcher (romhacking.net/utilities/704/)

xdelta3 command to create a patch:
```
xdelta3 -e -f -s original.iso modified.iso patch.xdelta
```

xdelta3 command to apply a patch:
```
xdelta3 -d -s original.iso patch.xdelta output.iso
```

---

## 3. PS2 ISO Requirements

### Sector Size
- PS2 ISOs use standard **2048-byte sectors** (ISO9660)
- DVD-based PS2 games use ISO9660+UDF hybrid filesystem

### SYSTEM.CNF
- Located at the ISO root directory
- Contains boot configuration: which ELF to execute, video mode, game version
- Example content for this game (expected):
  ```
  BOOT2 = cdrom0:\SLPM_653.78;1
  VER = 2.01
  VMODE = NTSC
  ```
- MUST be preserved exactly during ISO rebuild
- Some tools require SYSTEM.CNF to be the last file in directory order

### Boot Sector / PS2 Logo
- PS2 ISOs contain an encrypted PS2 logo check in the first sectors
- This logo data is checked by the PS2 BIOS on real hardware
- PCSX2 emulator typically skips this check
- Modifying the ISO structure can break the PS2 logo verification
- **Key insight:** Using pycdlib's in-place modification preserves the logo

---

## 4. Can pycdlib modify files in-place within an existing ISO?

**YES, with critical limitations.**

### Method: `modify_file_in_place()`
```python
iso = pycdlib.PyCdlib()
iso.open("original.iso")
iso.modify_file_in_place(
    BytesIO(new_data), len(new_data),
    iso_path="/PACKDATA.DIG;1"
)
iso.write("modified.iso")
iso.close()
```

### Limitations of `modify_file_in_place()`:
1. **Size constraint:** The new file can only grow within its current extent
   allocation. In ISO9660, an extent is almost always 2048 bytes. So a 48-byte
   file can only grow to 2048 bytes.
2. **For large files like PACKDATA.DIG:** The file already occupies many
   extents (hundreds of MB). The new file can be up to the current extent
   boundary of the original. If the modified PACKDATA.DIG is the **same size
   or smaller**, `modify_file_in_place()` works perfectly.
3. **If the file grows beyond its current allocation:** You must use the
   remove-and-re-add approach (see below).
4. Only files can be modified, not directories.
5. No files can be added or removed with this method alone.

### CRITICAL FOR THIS PROJECT:
PACKDATA.DIG will likely be the **exact same size** if we:
- Keep the same number of entries
- Pad each resource to the same sector boundaries
- Only change payload content (translated text, modified font atlases)

If the total size stays within the original's sector allocation,
`modify_file_in_place()` is the **safest and simplest approach**.

---

## 5. Alternative: Extract, replace, and rebuild?

**YES, this is the fallback approach.** Two sub-options:

### Option A: pycdlib rm_file + add_fp (recommended fallback)
```python
iso = pycdlib.PyCdlib()
iso.open("original.iso")

# Remove old file
iso.rm_file(iso_path="/PACKDATA.DIG;1")

# Add new file
with open("build/PACKDATA.DIG", "rb") as f:
    iso.add_fp(f, file_size, iso_path="/PACKDATA.DIG;1")

iso.write("build/BUSIN0_EN.iso")
iso.close()
```

**Pros:** Pure Python, no external tools, handles any file size.
**Cons:** Rewrites the entire ISO, may change file ordering/LBAs. This
could break games that use hardcoded sector addresses. Also may break
PS2 logo verification.

### Option B: mkisofs/genisoimage (if available)
```bash
# Extract all files from ISO
7z x "original.iso" -o"build/iso_staging/"

# Replace modified files
cp build/PACKDATA.DIG build/iso_staging/
cp build/SLPM_653.78 build/iso_staging/

# Rebuild
mkisofs -o build/BUSIN0_EN.iso \
  -V "SLPM_65378" \
  -sysid "PLAYSTATION" \
  build/iso_staging/
```

**Cons:** May not preserve PS2-specific boot sectors correctly.

### Option C: Ps2IsoTools (C# library)
- GitHub: https://github.com/Finzenku/Ps2IsoTools
- Specifically designed for PS2 ISOs with UDF filesystem
- Supports file replacement with Rebuild()
- Written in C#, available as NuGet package
- Would require .NET runtime, not ideal for this Python-based project

---

## 6. Original ISO

Path: `C:/Programmieren/wizardrytranslation/Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso`

**[NEEDS VERIFICATION]** Run to confirm ISO details:
```python
import pycdlib, io
iso = pycdlib.PyCdlib()
iso.open("C:/Programmieren/wizardrytranslation/Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso")
print("Volume ID:", iso.pvd.volume_identifier)
print("System ID:", iso.pvd.system_identifier)
print("Block size:", iso.pvd.log_block_size)
for child in iso.list_children(iso_path='/'):
    if not child.is_dot() and not child.is_dotdot():
        name = child.file_identifier.decode('ascii', errors='replace')
        print(f"  {name}  size={child.data_length}  lba={child.extent_location()}")
# Read SYSTEM.CNF
buf = io.BytesIO()
iso.get_file_from_iso_fp(buf, iso_path='/SYSTEM.CNF;1')
print("SYSTEM.CNF:", buf.getvalue().decode())
iso.close()
```

**Known from ARCHITECTURE_PLAN.md:** The ISO contains at minimum:
- `SYSTEM.CNF` -- boot configuration
- `SLPM_653.78` -- main game executable (ELF)
- `PACKDATA.DIG` -- all game resources (the main target for modification)

---

## 7. Does mkisofs or genisoimage exist on this system?

**[NEEDS VERIFICATION]** Run: `which mkisofs` / `where mkisofs` / `which genisoimage`

These are unlikely to be present on a stock Windows system. They come from:
- **cdrtools** (contains mkisofs) -- available via MSYS2, Chocolatey
- **genisoimage** -- Linux-native, rarely available on Windows
- **pycdlib-genisoimage** -- Python reimplementation included with pycdlib

If pycdlib is installed, `pycdlib-genisoimage` is available as a command-line
tool that emulates genisoimage behavior using pycdlib internally.

---

## 8. PS2 ISO Tools for Windows

| Tool | Platform | Notes |
|------|----------|-------|
| **pycdlib** (Python) | Cross-platform | Best option. Pure Python, handles ISO9660. modify_file_in_place for same-size replacements. |
| **Ps2IsoTools** (C#) | Windows/.NET | Purpose-built for PS2 UDF ISOs. Overkill if pycdlib works. |
| **mkisofs/cdrtools** | Windows (via MSYS2) | Standard ISO mastering tool. May not preserve PS2 boot correctly. |
| **UltraISO** | Windows | Commercial GUI tool. Can replace files in ISOs. Not scriptable. |
| **PowerISO** | Windows | Similar to UltraISO. Not scriptable. |
| **Apache ISO Creator** | Windows | GUI tool. |
| **ImgBurn** | Windows | Can build ISOs from files. Free. |
| **CDmage** | Windows | Legacy tool, can edit PS1/PS2 ISOs directly. |

---

## RECOMMENDED APPROACH

### Primary Strategy: pycdlib `modify_file_in_place()`

1. Install pycdlib: `pip install pycdlib`
2. Open the original ISO
3. Use `modify_file_in_place()` to replace PACKDATA.DIG (and SLPM_653.78 if the EXE is modified)
4. Write to a new ISO file
5. Create xdelta patch: `xdelta3 -e -f -s original.iso modified.iso patch.xdelta`

**This approach is safest because:**
- Preserves all ISO metadata, boot sectors, PS2 logo
- Preserves file LBAs (sector addresses) for all unmodified files
- No risk of breaking hardcoded sector references in the game
- Pure Python, no external tool dependencies (except xdelta3 for patching)

### Size Constraint Check
Before using `modify_file_in_place()`, verify that the modified PACKDATA.DIG
is not larger than the original. The PACKDATA rebuild script should ensure
sector-aligned packing that keeps total size identical.

If the modified PACKDATA.DIG is larger:
- Fallback to pycdlib rm_file + add_fp approach
- Test thoroughly in PCSX2 to ensure no LBA-dependent code breaks

### xdelta3 Installation
Download `xdelta3.exe` and place in project root or PATH. No installer needed.

---

## VERIFICATION COMMANDS TO RUN

When Bash access is available, run these commands to fill in the [NEEDS VERIFICATION] items:

```bash
# 1. Check pycdlib
pip show pycdlib

# 2. Check xdelta3
xdelta3 --version 2>&1 || echo "NOT INSTALLED"

# 3. Check mkisofs/genisoimage
which mkisofs 2>/dev/null || echo "mkisofs not found"
which genisoimage 2>/dev/null || echo "genisoimage not found"

# 4. Inspect ISO with pycdlib
python -c "
import pycdlib, io
iso = pycdlib.PyCdlib()
iso.open('C:/Programmieren/wizardrytranslation/Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso')
print('Volume:', iso.pvd.volume_identifier)
print('System:', iso.pvd.system_identifier)
print('Block size:', iso.pvd.log_block_size)
for c in iso.list_children(iso_path='/'):
    if not c.is_dot() and not c.is_dotdot():
        print(f'  {c.file_identifier.decode(\"ascii\",errors=\"replace\")}  size={c.data_length}  lba={c.extent_location()}')
buf = io.BytesIO()
iso.get_file_from_iso_fp(buf, iso_path='/SYSTEM.CNF;1')
print('SYSTEM.CNF:', buf.getvalue().decode())
iso.close()
"

# 5. Test modify_file_in_place feasibility
python -c "
import pycdlib
iso = pycdlib.PyCdlib()
iso.open('C:/Programmieren/wizardrytranslation/Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso')
rec = iso.get_record(iso_path='/PACKDATA.DIG;1')
print(f'PACKDATA.DIG: size={rec.data_length}, LBA={rec.extent_location()}')
# extent_length tells us max in-place size
print(f'Extent length (max in-place size): {rec.data_length}')
iso.close()
"
```
