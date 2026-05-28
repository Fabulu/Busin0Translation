#!/usr/bin/env python3
"""Debug PS2 GS packet structure in raw texture files."""
import struct
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")


def analyze_file(filename):
    data = open(os.path.join(TEX_DIR, filename), 'rb').read()
    tex = data[16:]  # skip sub-header
    total_qw = len(tex) // 16

    print(f"\n=== {filename}: {len(data)} bytes, tex={len(tex)} bytes, {total_qw} QWs ===")

    # Sub-header
    sh = struct.unpack_from('<IIII', data, 0)
    print(f"Sub-header: {sh}")

    # Walk through trying to parse GIF tags
    i = 0
    image_blocks = []

    while i < total_qw:
        lo = struct.unpack_from('<Q', tex, i * 16)[0]
        hi = struct.unpack_from('<Q', tex, i * 16 + 8)[0]

        nloop = lo & 0x7FFF
        eop = (lo >> 15) & 1
        flg = (lo >> 46) & 3
        nreg = (lo >> 60) & 0xF
        if nreg == 0:
            nreg = 16

        if flg == 2 and nloop > 0:
            # IMAGE mode
            end_qw = i + 1 + nloop
            if end_qw <= total_qw + 10:  # Allow small overflow
                data_start = (i + 1) * 16
                data_size = min(nloop * 16, len(tex) - data_start)
                image_blocks.append((data_start, data_size))
                print(f"  QW[{i:5d}] IMAGE: nloop={nloop}, data={data_start}-{data_start+data_size} ({data_size} bytes), EOP={eop}")
                i = min(end_qw, total_qw)
                continue

        if flg == 0 and nloop > 0:
            total_data_qw = nloop * nreg
            end_qw = i + 1 + total_data_qw

            if end_qw > total_qw:
                # This PACKED tag goes past end - not a real GIF tag
                print(f"  QW[{i:5d}] BAD PACKED: nloop={nloop} nreg={nreg} total={total_data_qw} "
                      f"(would end at QW {end_qw}, but only {total_qw} QWs exist)")
                # This is probably raw data, not a GIF tag
                # Try to see if there's an IMAGE tag nearby
                found = False
                for j in range(i + 1, min(i + 5, total_qw)):
                    lo2 = struct.unpack_from('<Q', tex, j * 16)[0]
                    flg2 = (lo2 >> 46) & 3
                    nloop2 = lo2 & 0x7FFF
                    if flg2 == 2 and nloop2 > 0 and j + 1 + nloop2 <= total_qw + 10:
                        print(f"  -> Found IMAGE at QW[{j}]")
                        i = j
                        found = True
                        break
                if not found:
                    # Remaining data is probably image data without GIF tags
                    remaining = (total_qw - i) * 16
                    print(f"  -> Remaining {remaining} bytes from offset {i*16} treated as raw data")
                    image_blocks.append((i * 16, remaining))
                    break
            else:
                print(f"  QW[{i:5d}] PACKED: nloop={nloop} nreg={nreg} total={total_data_qw} EOP={eop}")
                # Print A+D register writes
                for li in range(min(nloop, 2)):  # Just first 2 loops
                    for ri in range(nreg):
                        qi = i + 1 + li * nreg + ri
                        if qi < total_qw:
                            d_lo = struct.unpack_from('<Q', tex, qi * 16)[0]
                            d_hi = struct.unpack_from('<Q', tex, qi * 16 + 8)[0]
                            reg = d_hi & 0xFF
                            reg_names = {
                                0x06: 'TEX0_1', 0x50: 'BITBLTBUF', 0x51: 'TRXPOS',
                                0x52: 'TRXREG', 0x53: 'TRXDIR'
                            }
                            if reg in reg_names:
                                name = reg_names[reg]
                                extra = ""
                                if reg == 0x52:
                                    w = d_lo & 0xFFF
                                    h = (d_lo >> 32) & 0xFFF
                                    extra = f" ({w}x{h})"
                                elif reg == 0x50:
                                    dpsm = (d_lo >> 44) & 0x3F
                                    dbp = (d_lo >> 32) & 0x3FFF
                                    dbw = (d_lo >> 40) & 0x3F
                                    extra = f" (DBP={dbp} DBW={dbw} DPSM=0x{dpsm:02x})"
                                elif reg == 0x06:
                                    psm = (d_lo >> 20) & 0x3F
                                    tw = (d_lo >> 26) & 0xF
                                    th = (d_lo >> 30) & 0xF
                                    extra = f" (PSM=0x{psm:02x} {1<<tw}x{1<<th})"
                                print(f"      [{qi}] {name}: 0x{d_lo:016x}{extra}")
                i = end_qw
                continue

        # Not a recognizable GIF tag
        i += 1

    print(f"\nTotal IMAGE blocks: {len(image_blocks)}")
    total_image = sum(s for _, s in image_blocks)
    print(f"Total IMAGE data: {total_image} bytes")

    # For 512x512 PSMT8: 262144 + 1024 = 263168
    # For 512x64 PSMT8: 32768 + 1024 = 33792
    print(f"512x512 PSMT8 needs: {512*512 + 1024} bytes")
    print(f"512x64 PSMT8 needs: {512*64 + 1024} bytes")
    print(f"256x128 PSMT8 needs: {256*128 + 1024} bytes")


if __name__ == '__main__':
    for f in ['R2118_tavern_background.raw', 'R2119_tavern_buttons_1.raw']:
        analyze_file(f)
