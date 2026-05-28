#!/usr/bin/env python3
"""Analyze R2121 and R2122 raw data to understand the GIF packet structure."""
import struct, sys
sys.stdout.reconfigure(encoding='utf-8')

BASE = 'C:/Programmieren/wizardrytranslation/build/textures_to_edit'

for fname, label in [('R2121_guild_background.raw', 'R2121'),
                     ('R2122_guild_buttons.raw', 'R2122'),
                     ('R2118_tavern_background.raw', 'R2118')]:
    data = open(f'{BASE}/{fname}', 'rb').read()
    tex = data[16:]
    print(f'\n{"="*60}')
    print(f'{label}: {len(data)} bytes, tex={len(tex)} bytes')

    # Parse first GIF tag
    lo0 = struct.unpack_from('<Q', tex, 0)[0]
    nloop0 = lo0 & 0x7FFF
    flg0 = (lo0 >> 46) & 3
    nreg0 = (lo0 >> 60) & 0xF
    if nreg0 == 0: nreg0 = 16
    hdr_qws = 1 + nloop0 * nreg0
    print(f'First GIF: PACKED nloop={nloop0} nreg={nreg0} -> {hdr_qws} QWs = {hdr_qws*16} bytes')

    # Show QWs 17-22 (the data region start)
    print(f'\nQWs after header:')
    for qi in range(hdr_qws, min(hdr_qws + 10, len(tex) // 16)):
        lo = struct.unpack_from('<Q', tex, qi * 16)[0]
        hi = struct.unpack_from('<Q', tex, qi * 16 + 8)[0]
        nloop = lo & 0x7FFF
        flg = (lo >> 46) & 3
        nreg = (lo >> 60) & 0xF
        if nreg == 0: nreg = 16
        eop = (lo >> 15) & 1
        reg = hi & 0xFF

        # Check if this looks like a GIF tag
        tag_str = f'flg={flg} nloop={nloop} nreg={nreg} eop={eop}'

        # Check if hi byte looks like a register address (for A+D)
        if flg == 2:
            tag_str += ' IMAGE'
        elif flg == 0 and nloop > 0:
            tag_str += ' PACKED'

        print(f'  QW[{qi:5d}] lo={lo:016x} hi={hi:016x}  {tag_str}')

    # If PACKED mode follows, check what registers are written
    qi_next = hdr_qws
    lo_next = struct.unpack_from('<Q', tex, qi_next * 16)[0]
    flg_next = (lo_next >> 46) & 3
    nloop_next = lo_next & 0x7FFF
    nreg_next = (lo_next >> 60) & 0xF
    if nreg_next == 0: nreg_next = 16

    if flg_next == 0 and nloop_next > 0:
        total_ad = nloop_next * nreg_next
        end_qw = qi_next + 1 + total_ad
        remaining = len(tex) - end_qw * 16
        print(f'\nSecond GIF: PACKED nloop={nloop_next} nreg={nreg_next} -> {total_ad} A+D writes')
        print(f'  End QW: {end_qw}, remaining: {remaining} bytes')

        # Sample A+D writes
        reg_counts = {}
        for i in range(min(200, total_ad)):
            qi_ad = qi_next + 1 + i
            if qi_ad * 16 + 16 <= len(tex):
                d_hi = struct.unpack_from('<Q', tex, qi_ad * 16 + 8)[0]
                reg = d_hi & 0xFF
                reg_counts[reg] = reg_counts.get(reg, 0) + 1

        print(f'  First 200 register values: {dict(sorted(reg_counts.items()))}')

        # Check if register bytes are consistent (real A+D) or varied (pixel data)
        unique_regs = len(reg_counts)
        print(f'  Unique register values: {unique_regs}')
        if unique_regs > 20:
            print(f'  -> Likely misinterpreted pixel data (too many unique regs)')
        elif 0x54 in reg_counts:
            print(f'  -> Contains HWREG writes: {reg_counts[0x54]}')

    elif flg_next == 2:
        nloop_img = nloop_next
        print(f'\nSecond GIF: IMAGE nloop={nloop_img} (data size={nloop_img*16})')

    print()
