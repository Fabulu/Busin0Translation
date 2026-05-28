#!/usr/bin/env python3
"""Precisely count GIF tags and pixel data in R2118 and R2119."""
import struct
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")


def analyze(filename, tex_w, tex_h):
    data = open(os.path.join(TEX_DIR, filename), 'rb').read()
    sub_header = struct.unpack_from('<IIII', data, 0)
    payload_size = sub_header[1]
    tex = data[16:]

    print(f"\n{filename}: {len(data)} bytes, payload={payload_size}")
    print(f"  tex = {len(tex)} bytes = {len(tex)//16} QWs")
    print(f"  Target: {tex_w}x{tex_h} PSMT8 = {tex_w*tex_h} pixels + 1024 palette = {tex_w*tex_h + 1024}")

    # Scan for all potential GIF IMAGE tags (flg=2, reasonable nloop)
    # Only consider tags where nloop makes sense (< 1000 and doesn't overflow)
    total_qw = len(tex) // 16
    gif_tags = []
    pixel_bytes = 0

    i = 0
    while i < total_qw:
        lo = struct.unpack_from('<Q', tex, i * 16)[0]
        nloop = lo & 0x7FFF
        flg = (lo >> 46) & 3
        eop = (lo >> 15) & 1

        if flg == 2 and 0 < nloop <= 800 and i + 1 + nloop <= total_qw:
            gif_tags.append((i, nloop, eop))
            pixel_bytes += nloop * 16
            i += 1 + nloop
        elif flg == 0 and nloop > 0 and i == 0:
            # First PACKED block (header)
            nreg = (lo >> 60) & 0xF or 16
            total_data = nloop * nreg
            header_end = i + 1 + total_data
            print(f"  Header PACKED: QW[0..{header_end-1}] ({header_end} QWs = {header_end*16} bytes)")
            i = header_end
        else:
            i += 1

    print(f"  GIF IMAGE tags found: {len(gif_tags)}")
    print(f"  Total pixel data via IMAGE: {pixel_bytes} bytes")
    print(f"  GIF tag overhead: {len(gif_tags) * 16} bytes")

    if gif_tags:
        first_tag = gif_tags[0]
        last_tag = gif_tags[-1]
        print(f"  First IMAGE at QW[{first_tag[0]}], last at QW[{last_tag[0]}]")

        # Data before first IMAGE tag (after header)
        header_qws = first_tag[0]  # Everything before first IMAGE
        print(f"  QWs before first IMAGE: {header_qws} ({header_qws*16} bytes)")

        # Check if there are any non-GIF-tag QWs between IMAGE blocks
        gaps = []
        for idx in range(len(gif_tags) - 1):
            tag_i = gif_tags[idx]
            tag_next = gif_tags[idx + 1]
            end_of_data = tag_i[0] + 1 + tag_i[1]  # QW after last data QW
            gap_size = tag_next[0] - end_of_data
            if gap_size > 0:
                gaps.append((end_of_data, gap_size))
                print(f"  Gap: QW[{end_of_data}..{tag_next[0]-1}] = {gap_size} QWs ({gap_size*16} bytes)")
                # Show what's in the gap
                for qi in range(end_of_data, tag_next[0]):
                    d_lo = struct.unpack_from('<Q', tex, qi * 16)[0]
                    d_hi = struct.unpack_from('<Q', tex, qi * 16 + 8)[0]
                    print(f"    QW[{qi}]: {d_lo:016x} {d_hi:016x}")

        total_gap = sum(g[1] for g in gaps)
        print(f"  Total gap QWs: {total_gap} ({total_gap*16} bytes)")

        # Data after last IMAGE block
        last_end = last_tag[0] + 1 + last_tag[1]
        remaining = total_qw - last_end
        print(f"  QWs after last IMAGE: {remaining} ({remaining*16} bytes)")

    # Theory check: if we strip header (17 QWs = 272 bytes) and GIF tags,
    # how much pixel+palette data do we get?
    stripped_data = payload_size - 272 - len(gif_tags) * 16
    print(f"\n  payload - header(272) - tags({len(gif_tags)*16}) = {stripped_data}")
    print(f"  Need: {tex_w * tex_h + 1024}")

    # Theory check with header = 12 QWs = 192 bytes
    # In this case, QW[12-16] are part of pixel data, not header
    # And there are NO GIF tags (they're all pixel data)
    plain_data = payload_size - 192
    print(f"\n  payload - header(192) = {plain_data} (need {tex_w * tex_h + 1024})")

    # Check: does payload_size - 192 == tex_w * tex_h + 1024?
    if plain_data == tex_w * tex_h + 1024:
        print("  --> EXACT MATCH for 192-byte header, no GIF tags")


def main():
    analyze('R2118_tavern_background.raw', 512, 512)
    analyze('R2119_tavern_buttons_1.raw', 512, 64)
    analyze('R2120_tavern_buttons_2.raw', 512, 64)  # Same size as R2119
    analyze('R2121_guild_background.raw', 512, 512)  # Same size as R2118


if __name__ == '__main__':
    main()
