"""
Parse GS dump v2: analyze TBP0=0x319F draws and determine render target vs texture.

Key insight from v1: FRAME and XYOFFSET are set in the GS initial state (header),
not in the packet stream. We need to parse the GS dump header for initial register values.

GS dump format (PCSX2):
  - Header: initial GS register state + full 4MB VRAM
  - Packet stream: GIF transfers that modify state and draw primitives

GS privileged registers (in header at offset 0):
  0x00: PMODE, 0x20: SMODE1, 0x30: SMODE2, 0x70: DISPFB1, 0x80: DISPLAY1,
  0x90: DISPFB2, 0xA0: DISPLAY2, 0xE0: BGCOLOR, etc.

GS general registers (in header, usually at some offset):
  Each 64-bit register stored at 8-byte intervals or packed.

PCSX2 GS dump header structure (from PCSX2 source):
  - 8192 bytes: GS registers (privileged + general)
  - 4MB (4194304 bytes): VRAM
  - Then packet stream begins
  Total header = 8192 + 4194304 = 4202496 bytes
"""

import struct
import sys
import zstandard as zstd

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

GS_DUMP_PATH = r"C:\Users\Fabian Trunz\OneDrive - Berner Fachhochschule\Dokumente\PCSX2\snaps\Busin 0 - Wizardry Alternative Neo_SLPM-65378_20260602231607.gs.zst"

TARGET_TBP0 = 0x319F

# GIF register IDs
REG_PRIM  = 0x00
REG_RGBAQ = 0x01
REG_UV    = 0x03
REG_XYZF2 = 0x04
REG_XYZ2  = 0x05
REG_XYZ3  = 0x0D
REG_AD    = 0x0E

# GS register addresses
AD_TEX0_1     = 0x06
AD_TEX0_2     = 0x07
AD_XYOFFSET_1 = 0x18
AD_XYOFFSET_2 = 0x19
AD_FRAME_1    = 0x4C
AD_FRAME_2    = 0x4D
AD_BITBLTBUF  = 0x50
AD_TRXPOS     = 0x51
AD_TRXREG     = 0x52
AD_TRXDIR     = 0x53

PSM_NAMES = {0: 'PSMCT32', 1: 'PSMCT24', 2: 'PSMCT16', 0x13: 'PSMT8',
             0x14: 'PSMT4', 0x24: 'PSMT8H', 0x2C: 'PSMT4HL', 0x36: 'PSMT4HH'}

# Known chargen stat label Y positions (screen coords, from user)
STAT_LABELS = {
    107: "HP",
    133: "STR",
    159: "INT",
    185: "PIE",
    211: "VIT",
    237: "AGI",
    263: "LCK",
}
Y_TOLERANCE = 12


def decompress_gs_dump(path):
    with open(path, 'rb') as f:
        dctx = zstd.ZstdDecompressor()
        return dctx.decompress(f.read(), max_output_size=512 * 1024 * 1024)


def parse_tex0(val64):
    return {
        'tbp0': val64 & 0x3FFF,
        'tbw': (val64 >> 14) & 0x3F,
        'psm': (val64 >> 20) & 0x3F,
        'tw': 1 << ((val64 >> 26) & 0xF),
        'th': 1 << ((val64 >> 30) & 0xF),
        'raw': val64,
    }


def parse_frame(val64):
    return {
        'fbp': val64 & 0x1FF,
        'fbp_addr': (val64 & 0x1FF) * 32,
        'fbw': (val64 >> 16) & 0x3F,
        'psm': (val64 >> 24) & 0x3F,
        'fbmsk': (val64 >> 32) & 0xFFFFFFFF,
        'raw': val64,
    }


def parse_gs_header(data):
    """Parse the GS dump header for initial register state.

    PCSX2 GS dump format:
    - Offset 0: tag (4 bytes) - dump format version
    - Then: GS state snapshot
    - VRAM (4MB)
    - Packet stream

    The exact layout depends on PCSX2 version. Let's scan for known patterns.
    """
    print("Analyzing GS dump header...")
    print(f"  First 64 bytes: {data[:64].hex()}")

    # PCSX2 GS dump starts with a transfer type byte or a header
    # Let's look for the VRAM start by finding 4MB of data before the packet stream

    # The packet stream was found at offset 0xB79048 = 12,030,024
    # Total dump = 12,249,863 bytes
    # Packet stream size = 12,249,863 - 12,030,024 = 219,839 bytes
    # Before packet stream: 12,030,024 bytes
    # VRAM = 4MB = 4,194,304 bytes
    # So register header = 12,030,024 - 4,194,304 = 7,835,720 bytes
    # That's way too much for just registers. The format might be different.

    # Let's try another approach: look at the PCSX2 GS dump format
    # PCSX2 dumps: first byte indicates transfer type
    # But GS dumps have a different format...

    # Let's check: maybe the dump has multiple frames with VRAM between them
    # Or maybe PCSX2 uses a different header size

    # Actually PCSX2 gs dump format:
    # - First 8192 bytes: register state (see GSState)
    # - Then 4MB VRAM
    # - Then packet stream
    # Total header = 8192 + 4194304 = 4202496 = 0x401000

    header_size = 8192
    vram_size = 4 * 1024 * 1024  # 4MB
    expected_pkt_start = header_size + vram_size  # 4,202,496 = 0x401000

    print(f"  Expected packet stream start: 0x{expected_pkt_start:X} ({expected_pkt_start:,})")

    # But we found packet stream at 0xB79048 which is much later
    # Maybe there are multiple frames of VRAM? Or the header is larger?
    # Let's check if there are multiple VRAM snapshots

    # PCSX2 GS dump format (from source code GSCapture):
    # For each frame:
    #   type 0: GIF transfer (path + size + data)
    #   type 1: VSync
    #   type 2: ReadFIFO (size + data)
    #   type 3: Registers (just a marker)
    #
    # Actually the format starts with:
    #   - Privileged registers dump
    #   - General registers dump
    #   - VRAM
    #   - Then packet stream
    #
    # Let's try to find FRAME/TEX0/XYOFFSET values by scanning the header

    # GS internal registers are 64-bit each, addresses 0x00-0x7F (128 registers)
    # In the dump they might be stored as 128 * 8 = 1024 bytes for general regs
    # Plus privileged regs

    # Let's scan for register-like patterns in the header area
    print("\n  Scanning header for GS register values...")

    # Try to find FRAME_1 (addr 0x4C) and XYOFFSET_1 (addr 0x18) in the header
    # Registers might be stored at reg_addr * 8 or reg_addr * 16

    # Approach: scan the header region and look for plausible TEX0/FRAME values
    # TEX0 with TBP0=0x319F would have bits 0-13 = 0x319F

    results = {
        'frame_values': [],
        'tex0_values': [],
        'xyoffset_values': [],
    }

    # Scan first 16KB of header for register-like values
    scan_end = min(16384, len(data))
    for off in range(0, scan_end, 8):
        val = struct.unpack_from('<Q', data, off)[0]

        # Check if this looks like a FRAME register
        # FBP should be reasonable (0-511), FBW reasonable (0-31), PSM valid
        fbp = val & 0x1FF
        fbw = (val >> 16) & 0x3F
        psm = (val >> 24) & 0x3F
        fbmsk = (val >> 32) & 0xFFFFFFFF
        if fbp > 0 and fbw > 0 and psm in PSM_NAMES:
            fbp_addr = fbp * 32
            results['frame_values'].append((off, fbp, fbp_addr, fbw, psm, fbmsk, val))

        # Check for XYOFFSET
        ofx_raw = val & 0xFFFF
        ofy_raw = (val >> 32) & 0xFFFF
        if 1000 < ofx_raw < 40000 and 1000 < ofy_raw < 40000:
            ofx = ofx_raw / 16.0
            ofy = ofy_raw / 16.0
            if 100 < ofx < 2500 and 100 < ofy < 2500:
                results['xyoffset_values'].append((off, ofx, ofy, val))

    return results


def try_parse_chain(data, start, max_steps=50):
    pos = start
    steps = 0
    while pos < len(data) and steps < max_steps:
        t = data[pos]
        if t == 0:
            if pos + 6 > len(data): return steps
            path = data[pos + 1]
            size = struct.unpack_from('<I', data, pos + 2)[0]
            if path not in (1, 2, 3) or size > 10_000_000 or size == 0: return steps
            pos += 6 + size; steps += 1
        elif t == 1: pos += 2; steps += 1
        elif t == 2:
            if pos + 5 > len(data): return steps
            sz = struct.unpack_from('<I', data, pos + 1)[0]
            if sz > 10_000_000: return steps
            pos += 5 + sz; steps += 1
        elif t == 3: pos += 2; steps += 1
        else: return steps
    return steps


def find_packet_stream(data):
    print("  Scanning for packet stream start...")
    best_off = 0
    best_cl = 0
    for off in range(0, len(data), 10000):
        cl = try_parse_chain(data, off, 50)
        if cl > best_cl:
            best_cl = cl
            best_off = off

    lo = max(best_off - 10000, 0)
    final_off = best_off
    final_cl = best_cl
    for off in range(lo, best_off + 1):
        cl = try_parse_chain(data, off, 100)
        if cl > final_cl:
            final_cl = cl
            final_off = off

    print(f"  Packet stream at offset {final_off} (0x{final_off:X}), chain={final_cl}")
    return final_off, len(data)


def parse_packet_stream(data, seg_start, seg_end):
    """Parse packet stream, tracking TEX0, FRAME, XYOFFSET, BITBLTBUF, and draws."""
    pos = seg_start
    current_tex0 = None
    current_frame = None
    current_xyoffset = None
    draws_319f = []
    all_frame_writes = []
    all_tex0_values = {}
    all_xyoffsets = []
    all_bitblt = []
    pending_bitblt = {}
    frame_319f_active = False
    draws_into_319f = []
    packet_idx = 0

    # Also track ALL A+D writes to see what registers are written
    ad_register_counts = {}

    while pos < seg_end:
        t = data[pos]
        if t == 0:
            if pos + 6 > seg_end: break
            path = data[pos + 1]
            size = struct.unpack_from('<I', data, pos + 2)[0]
            if path not in (1, 2, 3) or size > 10_000_000:
                pos += 6 + size; packet_idx += 1; continue

            gif = data[pos + 6: pos + 6 + size]

            # Parse GIF for A+D writes and REGLIST draws
            gp = 0
            while gp + 16 <= len(gif):
                tag_lo = struct.unpack_from('<Q', gif, gp)[0]
                tag_hi = struct.unpack_from('<Q', gif, gp + 8)[0]
                nloop = tag_lo & 0x7FFF
                flg = (tag_lo >> 58) & 0x3
                nreg = (tag_lo >> 60) & 0xF
                if nreg == 0: nreg = 16
                eop = (tag_lo >> 15) & 1
                gp += 16

                if flg == 0:  # PACKED
                    regs = [(tag_hi >> (i * 4)) & 0xF for i in range(nreg)]
                    for _ in range(nloop):
                        for reg_id in regs:
                            if gp + 16 > len(gif): break
                            qw_lo = struct.unpack_from('<Q', gif, gp)[0]
                            qw_hi = struct.unpack_from('<Q', gif, gp + 8)[0]
                            gp += 16
                            if reg_id == REG_AD:
                                ad = qw_hi & 0xFF
                                ad_register_counts[ad] = ad_register_counts.get(ad, 0) + 1

                                if ad in (AD_TEX0_1, AD_TEX0_2):
                                    current_tex0 = parse_tex0(qw_lo)
                                    tbp0 = current_tex0['tbp0']
                                    if tbp0 not in all_tex0_values:
                                        all_tex0_values[tbp0] = current_tex0
                                elif ad in (AD_FRAME_1, AD_FRAME_2):
                                    frame = parse_frame(qw_lo)
                                    current_frame = frame
                                    all_frame_writes.append((frame, ad, packet_idx))
                                    if frame['fbp_addr'] == TARGET_TBP0:
                                        frame_319f_active = True
                                    else:
                                        frame_319f_active = False
                                elif ad in (AD_XYOFFSET_1, AD_XYOFFSET_2):
                                    ofx = (qw_lo & 0xFFFF) / 16.0
                                    ofy = ((qw_lo >> 32) & 0xFFFF) / 16.0
                                    current_xyoffset = (ofx, ofy)
                                    all_xyoffsets.append((ofx, ofy, ad, packet_idx))
                                elif ad == AD_BITBLTBUF:
                                    bbuf = qw_lo
                                    pending_bitblt['buf_raw'] = bbuf
                                    pending_bitblt['sbp'] = bbuf & 0x3FFF
                                    pending_bitblt['sbw'] = (bbuf >> 16) & 0x3F
                                    pending_bitblt['spsm'] = (bbuf >> 24) & 0x3F
                                    pending_bitblt['dbp'] = (bbuf >> 32) & 0x3FFF
                                    pending_bitblt['dbw'] = (bbuf >> 48) & 0x3F
                                    pending_bitblt['dpsm'] = (bbuf >> 56) & 0x3F
                                elif ad == AD_TRXDIR:
                                    xfer = dict(pending_bitblt)
                                    xfer['dir'] = qw_lo & 0x3
                                    xfer['packet_idx'] = packet_idx
                                    all_bitblt.append(xfer)
                                    if xfer.get('sbp') == TARGET_TBP0 or xfer.get('dbp') == TARGET_TBP0:
                                        pass  # will be checked later
                                    pending_bitblt = {}

                elif flg == 1:  # REGLIST
                    regs = [(tag_hi >> (i * 4)) & 0xF for i in range(nreg)]
                    has_uv = REG_UV in regs
                    has_xy = REG_XYZ2 in regs or REG_XYZF2 in regs or REG_XYZ3 in regs

                    if has_uv and has_xy and current_tex0:
                        uvs = []
                        xys_tl = []
                        xys_br = []
                        rgbaq = None
                        for li in range(nloop):
                            for reg_id in regs:
                                if gp + 8 > len(gif): break
                                val = struct.unpack_from('<Q', gif, gp)[0]
                                gp += 8
                                if reg_id == REG_UV:
                                    u = (val & 0x3FFF) / 16.0
                                    v = ((val >> 16) & 0x3FFF) / 16.0
                                    uvs.append((u, v))
                                elif reg_id == REG_XYZ3:
                                    x = (val & 0xFFFF) / 16.0
                                    y = ((val >> 16) & 0xFFFF) / 16.0
                                    xys_tl.append((x, y))
                                elif reg_id in (REG_XYZ2, REG_XYZF2):
                                    x = (val & 0xFFFF) / 16.0
                                    y = ((val >> 16) & 0xFFFF) / 16.0
                                    xys_br.append((x, y))
                                elif reg_id == REG_RGBAQ:
                                    rgbaq = val

                        if uvs:
                            draw = {
                                'tex0': dict(current_tex0),
                                'uvs': uvs,
                                'xys_tl': xys_tl,
                                'xys_br': xys_br,
                                'rgbaq': rgbaq,
                                'xyoffset': current_xyoffset,
                                'packet_idx': packet_idx,
                            }
                            if current_tex0['tbp0'] == TARGET_TBP0:
                                draws_319f.append(draw)
                            if frame_319f_active:
                                draws_into_319f.append(draw)
                    else:
                        tb = nloop * nreg * 8
                        if tb % 16: tb += 16 - (tb % 16)
                        gp += tb

                elif flg == 2:
                    gp += nloop * 16

                if eop: break

            pos += 6 + size
            packet_idx += 1
        elif t in (1, 3):
            pos += 2; packet_idx += 1
        elif t == 2:
            if pos + 5 > seg_end: break
            sz = struct.unpack_from('<I', data, pos + 1)[0]
            pos += 5 + sz; packet_idx += 1
        else:
            pos += 1; packet_idx += 1

    return {
        'draws_319f': draws_319f,
        'all_frame_writes': all_frame_writes,
        'all_tex0_values': all_tex0_values,
        'all_xyoffsets': all_xyoffsets,
        'all_bitblt': all_bitblt,
        'draws_into_319f': draws_into_319f,
        'ad_register_counts': ad_register_counts,
        'total_packets': packet_idx,
    }


def scan_header_for_registers(data, pkt_start):
    """Scan the GS dump header area for initial register state."""
    print(f"\n{'=' * 130}")
    print("GS DUMP HEADER ANALYSIS")
    print(f"{'=' * 130}")

    # The header is everything before the packet stream
    header = data[:pkt_start]
    print(f"Header size: {len(header):,} bytes (0x{len(header):X})")

    # PCSX2 GS dump structure (from GSCaptureDev.cpp):
    # The dump contains:
    # 1. A "freeze" snapshot of GS state
    # 2. Optionally VRAM
    # 3. Packet stream
    #
    # The freeze data includes the GS internal registers.
    # Let's look for known register layouts.

    # GS has 128 general-purpose registers (0x00-0x7F), each 64 bits
    # In PCSX2's GSState, these are stored as an array
    # Common layout: regs at some offset, then VRAM (4MB)

    # Let's try scanning for plausible XYOFFSET values
    # XYOFFSET for PS2 typically has OFX and OFY around 1700-2000 range
    # In 12.4 fixed point: 1778 * 16 = 28448 = 0x6F20

    print("\n  Searching for XYOFFSET-like values (OFX ~1700-2000)...")
    xyoffset_candidates = []
    for off in range(0, min(len(header), 32768), 8):
        val = struct.unpack_from('<Q', data, off)[0]
        ofx_raw = val & 0xFFFF
        zero_check = (val >> 16) & 0xFFFF  # should be 0 between OFX and OFY
        ofy_raw = (val >> 32) & 0xFFFF
        zero_check2 = (val >> 48) & 0xFFFF  # should be 0

        ofx = ofx_raw / 16.0
        ofy = ofy_raw / 16.0

        if (1600 < ofx < 2200 and 1600 < ofy < 2200
            and zero_check == 0 and zero_check2 == 0):
            xyoffset_candidates.append((off, ofx, ofy, val))

    for off, ofx, ofy, val in xyoffset_candidates:
        print(f"    offset 0x{off:04X}: OFX={ofx:.1f}, OFY={ofy:.1f} (raw=0x{val:016X})")

    # Search for FRAME register values
    print("\n  Searching for FRAME-like values...")
    frame_candidates = []
    for off in range(0, min(len(header), 32768), 8):
        val = struct.unpack_from('<Q', data, off)[0]
        fbp = val & 0x1FF
        reserved1 = (val >> 9) & 0x7F  # bits 9-15 should be 0
        fbw = (val >> 16) & 0x3F
        reserved2 = (val >> 22) & 0x3  # bits 22-23 should be 0
        psm = (val >> 24) & 0x3F
        reserved3 = (val >> 30) & 0x3  # bits 30-31 should be 0
        fbmsk = (val >> 32) & 0xFFFFFFFF

        fbp_addr = fbp * 32
        if (fbp > 0 and fbw > 0 and reserved1 == 0 and reserved2 == 0
            and reserved3 == 0 and psm in (0, 1, 2)):
            frame_candidates.append((off, fbp, fbp_addr, fbw, psm, fbmsk, val))

    for off, fbp, fbp_addr, fbw, psm, fbmsk, val in frame_candidates:
        psm_name = PSM_NAMES.get(psm, f"0x{psm:02X}")
        match = " <<<< MATCH 0x319F!" if fbp_addr == TARGET_TBP0 else ""
        print(f"    offset 0x{off:04X}: FBP={fbp} (0x{fbp_addr:04X}) FBW={fbw} PSM={psm_name} FBMSK=0x{fbmsk:08X}{match}")

    # Search for TEX0 with TBP0=0x319F
    print(f"\n  Searching for TEX0 with TBP0=0x{TARGET_TBP0:04X}...")
    for off in range(0, min(len(header), 32768), 8):
        val = struct.unpack_from('<Q', data, off)[0]
        tbp0 = val & 0x3FFF
        if tbp0 == TARGET_TBP0:
            tex0 = parse_tex0(val)
            psm_name = PSM_NAMES.get(tex0['psm'], f"0x{tex0['psm']:02X}")
            print(f"    offset 0x{off:04X}: TBP0=0x{tbp0:04X} TBW={tex0['tbw']} PSM={psm_name} "
                  f"size={tex0['tw']}x{tex0['th']} raw=0x{val:016X}")

    # Also dump raw bytes at key offsets to understand the layout
    print("\n  Raw header structure (first 256 bytes):")
    for off in range(0, 256, 16):
        hex_str = data[off:off+16].hex()
        # Format nicely
        hex_pairs = ' '.join(hex_str[i:i+2] for i in range(0, len(hex_str), 2))
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[off:off+16])
        print(f"    0x{off:04X}: {hex_pairs}  {ascii_str}")

    return xyoffset_candidates


def gs_to_screen(gs_x, gs_y, xyoffset):
    if xyoffset:
        return gs_x - xyoffset[0], gs_y - xyoffset[1]
    return gs_x - 1778.0, gs_y - 1841.0  # fallback


def match_stat_label(sy):
    for target_y, label in STAT_LABELS.items():
        if abs(sy - target_y) < Y_TOLERANCE:
            return label
    return None


def main():
    print("=" * 130)
    print("GS DUMP ANALYSIS v2: TBP0=0x319F (with header parsing)")
    print("=" * 130)

    print("\nDecompressing GS dump...")
    data = decompress_gs_dump(GS_DUMP_PATH)
    print(f"Decompressed: {len(data):,} bytes")

    print("\nFinding packet stream...")
    pkt_start, pkt_end = find_packet_stream(data)

    # Parse header for initial register state
    xyoffset_candidates = scan_header_for_registers(data, pkt_start)

    # Determine XYOFFSET to use
    if xyoffset_candidates:
        # Use first valid candidate
        _, ofx, ofy, _ = xyoffset_candidates[0]
        xyoffset = (ofx, ofy)
    else:
        xyoffset = (1778.0, 1841.0)
    print(f"\nUsing XYOFFSET: ({xyoffset[0]:.1f}, {xyoffset[1]:.1f})")

    # Parse packet stream
    print("\nParsing packet stream...")
    result = parse_packet_stream(data, pkt_start, pkt_end)

    print(f"Total packets: {result['total_packets']}")

    # ===== A+D register usage =====
    print(f"\n{'=' * 130}")
    print("A+D REGISTER WRITE COUNTS (in packet stream)")
    print(f"{'=' * 130}")
    reg_names = {
        0x00: 'PRIM', 0x01: 'RGBAQ', 0x02: 'ST', 0x03: 'UV',
        0x04: 'XYZF2', 0x05: 'XYZ2', 0x06: 'TEX0_1', 0x07: 'TEX0_2',
        0x08: 'CLAMP_1', 0x09: 'CLAMP_2', 0x0A: 'FOG',
        0x14: 'TEX1_1', 0x15: 'TEX1_2', 0x16: 'TEX2_1', 0x17: 'TEX2_2',
        0x18: 'XYOFFSET_1', 0x19: 'XYOFFSET_2',
        0x1A: 'PRMODECONT', 0x1B: 'PRMODE', 0x1C: 'TEXCLUT',
        0x22: 'SCANMSK', 0x34: 'MIPTBP1_1', 0x35: 'MIPTBP1_2',
        0x36: 'MIPTBP2_1', 0x37: 'MIPTBP2_2',
        0x3B: 'TEXA', 0x3D: 'FOGCOL', 0x3F: 'TEXFLUSH',
        0x40: 'SCISSOR_1', 0x41: 'SCISSOR_2',
        0x42: 'ALPHA_1', 0x43: 'ALPHA_2',
        0x44: 'DIMX', 0x45: 'DTHE', 0x46: 'COLCLAMP',
        0x47: 'TEST_1', 0x48: 'TEST_2',
        0x49: 'PABE', 0x4A: 'FBA_1', 0x4B: 'FBA_2',
        0x4C: 'FRAME_1', 0x4D: 'FRAME_2',
        0x4E: 'ZBUF_1', 0x4F: 'ZBUF_2',
        0x50: 'BITBLTBUF', 0x51: 'TRXPOS', 0x52: 'TRXREG', 0x53: 'TRXDIR',
        0x60: 'HWREG', 0x61: 'SIGNAL', 0x62: 'FINISH', 0x63: 'LABEL',
    }
    for ad, count in sorted(result['ad_register_counts'].items()):
        name = reg_names.get(ad, f'???')
        marker = ""
        if ad in (AD_FRAME_1, AD_FRAME_2): marker = " <-- FRAME"
        if ad in (AD_XYOFFSET_1, AD_XYOFFSET_2): marker = " <-- XYOFFSET"
        print(f"  0x{ad:02X} ({name:>14}): {count:>5} writes{marker}")

    # ===== TEX0 values =====
    print(f"\n{'=' * 130}")
    print(f"ALL UNIQUE TEX0 VALUES ({len(result['all_tex0_values'])})")
    print(f"{'=' * 130}")
    for tbp0 in sorted(result['all_tex0_values'].keys()):
        t = result['all_tex0_values'][tbp0]
        psm_name = PSM_NAMES.get(t['psm'], f"0x{t['psm']:02X}")
        marker = " <<<< TARGET" if tbp0 == TARGET_TBP0 else ""
        print(f"  TBP0=0x{tbp0:04X}  TBW={t['tbw']:>2}  PSM={psm_name:<8}  "
              f"size={t['tw']:>4}x{t['th']:<4}{marker}")

    # ===== XYOFFSET writes =====
    print(f"\n{'=' * 130}")
    print(f"XYOFFSET WRITES IN PACKET STREAM")
    print(f"{'=' * 130}")
    if result['all_xyoffsets']:
        for ofx, ofy, ad, pidx in result['all_xyoffsets']:
            reg_name = "XYOFFSET_1" if ad == AD_XYOFFSET_1 else "XYOFFSET_2"
            print(f"  {reg_name}: OFX={ofx:.1f}, OFY={ofy:.1f} (packet #{pidx})")
            # Update xyoffset if found
            xyoffset = (ofx, ofy)
    else:
        print("  No XYOFFSET writes in packet stream (using header value)")

    # ===== FRAME writes =====
    print(f"\n{'=' * 130}")
    print(f"FRAME REGISTER WRITES")
    print(f"{'=' * 130}")
    print(f"Total FRAME writes in packet stream: {len(result['all_frame_writes'])}")

    unique_frames = {}
    for frame, ad, pidx in result['all_frame_writes']:
        key = frame['raw']
        if key not in unique_frames:
            unique_frames[key] = (frame, ad, pidx)

    if unique_frames:
        print(f"Unique FRAME values: {len(unique_frames)}")
        for raw in sorted(unique_frames.keys()):
            frame, ad, pidx = unique_frames[raw]
            psm_name = PSM_NAMES.get(frame['psm'], f"0x{frame['psm']:02X}")
            match = " <<<< 0x319F RENDER TARGET!" if frame['fbp_addr'] == TARGET_TBP0 else ""
            reg_name = "FRAME_1" if ad == AD_FRAME_1 else "FRAME_2"
            print(f"  {reg_name}: FBP=0x{frame['fbp_addr']:04X} FBW={frame['fbw']} PSM={psm_name} "
                  f"FBMSK=0x{frame['fbmsk']:08X}{match}")
    else:
        print("  No FRAME writes found in packet stream")
        print("  FRAME is set in the initial GS state (header)")

    # Check frame writes targeting 0x319F
    frame_319f = [(f, a, p) for f, a, p in result['all_frame_writes'] if f['fbp_addr'] == TARGET_TBP0]
    print(f"\n  FRAME writes with FBP=0x{TARGET_TBP0:04X}: {len(frame_319f)}")

    # ===== BITBLTBUF =====
    print(f"\n{'=' * 130}")
    print(f"BITBLTBUF TRANSFERS")
    print(f"{'=' * 130}")
    print(f"Total transfers: {len(result['all_bitblt'])}")

    bitblt_319f = [x for x in result['all_bitblt']
                   if x.get('sbp') == TARGET_TBP0 or x.get('dbp') == TARGET_TBP0]
    print(f"Transfers involving 0x{TARGET_TBP0:04X}: {len(bitblt_319f)}")

    # Show all transfers for context
    if result['all_bitblt']:
        print("\n  All transfers:")
        dir_names = {0: 'host->local', 1: 'local->host', 2: 'local->local'}
        for xfer in result['all_bitblt']:
            sbp = xfer.get('sbp', 0)
            dbp = xfer.get('dbp', 0)
            direction = xfer.get('dir', 0)
            match = ""
            if sbp == TARGET_TBP0: match = " <<<< SRC=0x319F"
            if dbp == TARGET_TBP0: match = " <<<< DST=0x319F"
            print(f"    SBP=0x{sbp:04X} -> DBP=0x{dbp:04X}  dir={dir_names.get(direction, '?')}{match}")

    # ===== DRAWS FROM 0x319F =====
    print(f"\n{'=' * 130}")
    print(f"DRAWS USING TEX0.TBP0=0x{TARGET_TBP0:04X}")
    print(f"{'=' * 130}")
    print(f"Total draws: {len(result['draws_319f'])}")

    if result['draws_319f']:
        t = result['draws_319f'][0]['tex0']
        psm_name = PSM_NAMES.get(t['psm'], f"0x{t['psm']:02X}")
        print(f"Texture: TBP0=0x{t['tbp0']:04X} TBW={t['tbw']} PSM={psm_name} "
              f"size={t['tw']}x{t['th']}")
        print(f"XYOFFSET: ({xyoffset[0]:.1f}, {xyoffset[1]:.1f})")

        draws_sorted = sorted(result['draws_319f'], key=lambda d: (
            d['xys_tl'][0][1] if d['xys_tl'] else (d['xys_br'][0][1] if d['xys_br'] else 0),
            d['xys_tl'][0][0] if d['xys_tl'] else (d['xys_br'][0][0] if d['xys_br'] else 0),
        ))

        print(f"\n{'#':>3}  {'UV TL':>14}  {'UV BR':>14}  {'UV Size':>8}  "
              f"{'GS TL':>14}  {'GS BR':>14}  {'Screen TL':>14}  {'Screen BR':>14}  {'Scr Size':>10}  {'Label'}")
        print("-" * 150)

        for i, d in enumerate(draws_sorted):
            uvs = d['uvs']
            # Use the draw's own xyoffset if available, else the global one
            draw_xyoff = d.get('xyoffset') or xyoffset

            if len(uvs) >= 2:
                u_tl, v_tl = uvs[0]
                u_br, v_br = uvs[1]
                uv_w = u_br - u_tl
                uv_h = v_br - v_tl
            else:
                continue

            gs_tl = scr_tl = scr_br = scr_sz = "N/A"
            gs_br_str = "N/A"
            sx_tl = sy_tl = None

            if d['xys_tl']:
                gx, gy = d['xys_tl'][0]
                gs_tl = f"({gx:.0f},{gy:.0f})"
                sx_tl, sy_tl = gs_to_screen(gx, gy, draw_xyoff)
                scr_tl = f"({sx_tl:.0f},{sy_tl:.0f})"

            if d['xys_br']:
                gx2, gy2 = d['xys_br'][0]
                gs_br_str = f"({gx2:.0f},{gy2:.0f})"
                sx_br, sy_br = gs_to_screen(gx2, gy2, draw_xyoff)
                scr_br = f"({sx_br:.0f},{sy_br:.0f})"
                if sx_tl is not None:
                    scr_sz = f"{sx_br-sx_tl:.0f}x{sy_br-sy_tl:.0f}"

            label = ""
            if sy_tl is not None:
                m = match_stat_label(sy_tl)
                if m: label = f"<- {m}"

            print(f"{i:>3}  ({u_tl:6.1f},{v_tl:5.1f})  ({u_br:6.1f},{v_br:5.1f})  "
                  f"{uv_w:3.0f}x{uv_h:<3.0f}  {gs_tl:>14}  {gs_br_str:>14}  "
                  f"{scr_tl:>14}  {scr_br:>14}  {scr_sz:>10}  {label}")

    # ===== DRAWS INTO 0x319F =====
    print(f"\n{'=' * 130}")
    print(f"DRAWS RENDERED INTO 0x{TARGET_TBP0:04X}")
    print(f"{'=' * 130}")
    print(f"Total: {len(result['draws_into_319f'])}")
    if result['draws_into_319f']:
        for i, d in enumerate(result['draws_into_319f'][:50]):
            t = d['tex0']
            uvs = d['uvs']
            if len(uvs) >= 2:
                u_tl, v_tl = uvs[0]
                u_br, v_br = uvs[1]
            else:
                continue
            print(f"  [{i}] src TBP0=0x{t['tbp0']:04X} UV=({u_tl:.1f},{v_tl:.1f})-({u_br:.1f},{v_br:.1f})")

    # ===== CONCLUSION =====
    print(f"\n{'=' * 130}")
    print(f"CONCLUSION")
    print(f"{'=' * 130}")

    print(f"\n  TBP0 = 0x{TARGET_TBP0:04X}")
    print(f"  FRAME writes targeting it: {len(frame_319f)}")
    print(f"  BITBLTBUF transfers to it: {len(bitblt_319f)}")
    print(f"  Draws FROM it (as texture): {len(result['draws_319f'])}")
    print(f"  Draws INTO it (as render target): {len(result['draws_into_319f'])}")

    if len(frame_319f) > 0:
        print(f"\n  VERDICT: 0x319F IS a render target.")
    elif len(bitblt_319f) > 0:
        print(f"\n  VERDICT: 0x319F receives data via VRAM transfer (BITBLTBUF).")
    else:
        print(f"\n  VERDICT: No FRAME or BITBLTBUF writes to 0x319F found in the packet stream.")
        print(f"  This means EITHER:")
        print(f"    a) 0x319F was set up as a render target BEFORE the GS dump capture started")
        print(f"       (composition happened in a prior frame)")
        print(f"    b) 0x319F is a regular texture uploaded via CPU->VRAM transfer that")
        print(f"       was already in VRAM when the dump was captured")
        print(f"  ")
        print(f"  Since the texture is PSMT4 256x256 and shows at stat label positions,")
        print(f"  and the game has VRAM transfers in this dump, it likely was pre-composed.")


if __name__ == '__main__':
    main()
