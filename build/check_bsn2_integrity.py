"""
Check if BSN2_0.DSI was correctly relocated in the ISO.
The game engine might have hardcoded LBA references to BSN2_0.DSI
in the EXE or in another resource file. If it reads audio from the
OLD LBA, it would hit the end of the enlarged PACKDATA instead.
"""
import struct, os

os.chdir('C:/Programmieren/wizardrytranslation')
SECTOR = 2048

# Original BSN2_0.DSI LBA
ORIG_BSN2_LBA = 426020
# Shifted BSN2_0.DSI LBA
NEW_BSN2_LBA = 426106
SHIFT = NEW_BSN2_LBA - ORIG_BSN2_LBA

print(f"BSN2_0.DSI shift: {ORIG_BSN2_LBA} -> {NEW_BSN2_LBA} (+{SHIFT} sectors)")

# Search the EXE for the original BSN2_0 LBA value
exe_path = 'build/SLPM_653.78_patched'
if not os.path.exists(exe_path):
    exe_path = 'extracted/SLPM_653.78'

exe = open(exe_path, 'rb').read()
lba_le = struct.pack('<I', ORIG_BSN2_LBA)
lba_be = struct.pack('>I', ORIG_BSN2_LBA)

print(f"\nSearching EXE for hardcoded BSN2_0 LBA ({ORIG_BSN2_LBA} = 0x{ORIG_BSN2_LBA:X}):")
matches = []
for i in range(len(exe) - 3):
    if exe[i:i+4] == lba_le:
        matches.append(('LE', i))
    elif exe[i:i+4] == lba_be:
        matches.append(('BE', i))

if matches:
    for endian, off in matches:
        ctx = exe[max(0,off-8):off+12]
        print(f"  Found at 0x{off:06X} ({endian}): context = {ctx.hex()}")
else:
    print("  Not found in EXE")

# Also search for PACKDATA LBA and size
pack_lba = 16029
pack_lba_le = struct.pack('<I', pack_lba)
print(f"\nSearching EXE for PACKDATA LBA ({pack_lba}):")
for i in range(len(exe) - 3):
    if exe[i:i+4] == pack_lba_le:
        print(f"  Found at 0x{i:06X}")

# Search for sector offset of PACKDATA.DIG in the EXE
# The game might load resources by calculating: PACKDATA_LBA + resource_sector_offset
# Check if any resource's sector offset appears in the EXE as a hardcoded value

# Also check: the game loads PACKDATA via ISO filesystem or via hardcoded sector?
# PS2 games typically use the ISO filesystem for initial file lookup,
# then use the LBA + offset for streaming reads

# Check: does the IOP module load audio by LBA or by filename?
# BSN2_0.DSI is likely loaded by the IOP for streaming audio
# The IOP modules use cdvdReadChain or similar, which takes LBA+sector_count

# Search for the other file LBAs that were shifted
print(f"\nSearching EXE for ALL shifted file LBAs:")
shifted_lbas = {
    'BSN2_0.DSI': 426020,
    'PADMAN.IRX': 456954,
    'SIO2MAN.IRX': 456976,
    'MCSERV.IRX': 456980,
    'MODMIDI.IRX': 456984,
    'MUS.IRX': 456995,
    'LIBSD.IRX': 457007,
    'MODMSIN.IRX': 457021,
    'MODHSYN.IRX': 457022,
    'MCMAN.IRX': 457052,
    'IOPRP254.IMG': 457099,
    'SLPM_653.78': 457143,
    'SYSTEM.CNF': 457273,
}

for name, lba in shifted_lbas.items():
    lba_bytes = struct.pack('<I', lba)
    count = 0
    for i in range(len(exe) - 3):
        if exe[i:i+4] == lba_bytes:
            count += 1
    if count > 0:
        print(f"  {name} (LBA {lba}): {count} matches in EXE")

# Critical: search PACKDATA itself for BSN2_0 LBA references
# Some games store audio segment tables in the main data file
print(f"\nSearching PACKDATA header (first 125 sectors) for BSN2_0 LBA:")
with open('build/PACKDATA_broken.DIG', 'rb') as f:
    hdr = f.read(125 * SECTOR)
    for i in range(len(hdr) - 3):
        if hdr[i:i+4] == lba_le:
            print(f"  Found at PACKDATA offset 0x{i:06X}")

# Check the original PACKDATA too
print(f"\nSearching original PACKDATA header for BSN2_0 LBA:")
with open('extracted/PACKDATA.DIG', 'rb') as f:
    hdr = f.read(125 * SECTOR)
    for i in range(len(hdr) - 3):
        if hdr[i:i+4] == lba_le:
            print(f"  Found at original PACKDATA offset 0x{i:06X}")

# One more thing: check if BSN2_0 is referenced by sector offset RELATIVE to ISO start
# or relative to PACKDATA.DIG. The game's audio system might read it via cdvdRead
# using an absolute LBA.
print(f"\nKey finding: If the game reads BSN2_0.DSI via ISO filesystem (sceCdSearchFile),")
print(f"the relocated LBA is fine because the directory was updated.")
print(f"If it uses a hardcoded LBA, it will read wrong data.")
