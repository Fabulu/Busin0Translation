"""Extract R2100 and R1370 from PACKDATA.DIG as standalone files.

R2100 and R1370 are 'outlier' resources stored in sectors 17-84 and 85-124
respectively, before the main resource area. They were previously skipped
by extract_packdata_raw.py.

Also extracts the 4 individual sub-block pixel data regions from R2100.
"""
import struct
import os
import sys

DIG_PATH  = r'C:\Programmieren\wizardrytranslation\extracted\PACKDATA.DIG'
OUT_DIR   = r'C:\Programmieren\wizardrytranslation\extracted\packdata_raw'
SECTOR    = 2048

os.makedirs(OUT_DIR, exist_ok=True)

with open(DIG_PATH, 'rb') as f:
    # ── Read TOC entries for R2100 and R1370 ──
    toc_data = f.read(2883 * 12)

    for idx in (2100, 1370):
        so, sc, tc = struct.unpack_from('<III', toc_data, idx * 12)
        byte_off  = so * SECTOR
        byte_size = sc * SECTOR
        byte_end  = byte_off + byte_size

        print(f'R{idx}: TOC sector_offset={so} (0x{so:X}), sector_count={sc} (0x{sc:X}), type={tc}')
        print(f'  byte range: {byte_off} .. {byte_end - 1}  ({byte_size} bytes)')

        f.seek(byte_off)
        raw = f.read(byte_size)
        assert len(raw) == byte_size, f'Short read for R{idx}'

        out_path = os.path.join(OUT_DIR, f'{idx:04d}_type{tc:02d}.raw')
        with open(out_path, 'wb') as out:
            out.write(raw)
        print(f'  -> {out_path}  ({len(raw)} bytes)')

    # ── Parse R2100 sub-blocks ──
    print('\n--- R2100 sub-block analysis ---')
    so2100, sc2100, _ = struct.unpack_from('<III', toc_data, 2100 * 12)
    f.seek(so2100 * SECTOR)
    r2100 = f.read(sc2100 * SECTOR)

    # 64-byte descriptor table: 4 entries x 16 bytes each
    #   [0] u32 sub_index
    #   [4] u32 sub_total_size (including 64-byte GIF header)
    #   [8] u32 data_offset   (from start of R2100)
    #  [12] u32 padding (0)
    NUM_SUBS = 4
    print(f'Descriptor table (first {NUM_SUBS * 16} bytes):')
    for i in range(NUM_SUBS):
        sub_idx, sub_size, data_off, pad = struct.unpack_from('<IIII', r2100, i * 16)
        print(f'  Sub {i}: index={sub_idx}, total_size=0x{sub_size:X} ({sub_size}), '
              f'data_offset=0x{data_off:X} ({data_off})')

    # Each sub-block: 64-byte GIF tag header + pixel data
    GIF_HDR_SIZE = 64
    PIXEL_SIZE   = 32768   # 0x8000, from header field at sub+0x30

    for i in range(NUM_SUBS):
        sub_idx, sub_size, data_off, _ = struct.unpack_from('<IIII', r2100, i * 16)

        # Verify the 64-byte sub-header is identical across all subs
        hdr = r2100[data_off:data_off + GIF_HDR_SIZE]
        pixel_size_field = struct.unpack_from('<I', hdr, 0x30)[0]
        print(f'\n  Sub {i}: GIF header at R2100+0x{data_off:X}')
        print(f'    pixel_size field at hdr+0x30 = 0x{pixel_size_field:X} ({pixel_size_field})')

        pixel_off = data_off + GIF_HDR_SIZE
        pixel_data = r2100[pixel_off:pixel_off + PIXEL_SIZE]
        assert len(pixel_data) == PIXEL_SIZE, f'Short pixel data for sub {i}'

        abs_r2100_offset = so2100 * SECTOR
        print(f'    Pixel data: R2100+0x{pixel_off:X}  (PACKDATA abs 0x{abs_r2100_offset + pixel_off:X})')
        print(f'    Size: {PIXEL_SIZE} bytes (0x{PIXEL_SIZE:X})')

        out_path = os.path.join(OUT_DIR, f'r2100_sub{i}_pixels.bin')
        with open(out_path, 'wb') as out:
            out.write(pixel_data)
        print(f'    -> {out_path}')

        # Tail data after pixels
        tail_size = sub_size - GIF_HDR_SIZE - PIXEL_SIZE
        print(f'    Tail data after pixels: {tail_size} bytes (palette/GIF transfer tags)')

    # ── Verify sub-headers match across all 4 subs ──
    print('\n--- Sub-header consistency check ---')
    hdrs = []
    for i in range(NUM_SUBS):
        _, _, data_off, _ = struct.unpack_from('<IIII', r2100, i * 16)
        hdrs.append(r2100[data_off:data_off + GIF_HDR_SIZE])

    all_match = all(h == hdrs[0] for h in hdrs[1:])
    print(f'All 4 sub-block 64-byte headers identical: {all_match}')
    if all_match:
        print('Header bytes:')
        for r in range(0, GIF_HDR_SIZE, 16):
            hex_str = ' '.join(f'{b:02X}' for b in hdrs[0][r:r+16])
            print(f'  {r:04X}: {hex_str}')

    # ── Quick check on R1370 structure ──
    print('\n--- R1370 structure peek ---')
    so1370, sc1370, _ = struct.unpack_from('<III', toc_data, 1370 * 12)
    f.seek(so1370 * SECTOR)
    r1370 = f.read(sc1370 * SECTOR)
    print(f'R1370 first 64 bytes:')
    for r in range(0, 64, 16):
        hex_str = ' '.join(f'{b:02X}' for b in r1370[r:r+16])
        print(f'  {r:04X}: {hex_str}')

    # Check if R1370 has the same descriptor table format
    vals = struct.unpack_from('<4I', r1370, 0)
    print(f'First 4 uint32: {vals}')

print('\nDone.')
