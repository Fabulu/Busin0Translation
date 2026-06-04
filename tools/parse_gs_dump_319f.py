"""
Parse GS dump to analyze TBP0=0x319F:
1. Extract ALL draws that use TEX0.TBP0=0x319F
2. Check if FRAME.FBP=0x319F (render target detection)
3. Map screen positions to chargen stat labels
4. Determine if 0x319F is a render target or a disc-loaded texture

GS register addresses:
  0x06 = TEX0_1     (texture base pointer for context 1)
  0x07 = TEX0_2     (texture base pointer for context 2)
  0x4C = FRAME_1    (frame buffer base pointer for context 1)
  0x4D = FRAME_2    (frame buffer base pointer for context 2)
  0x18 = XYOFFSET_1
  0x19 = XYOFFSET_2
  0x50 = BITBLTBUF  (GS transfer source/dest)
  0x52 = TRXDIR     (transfer direction: 0=host->local, 1=local->host, 2=local->local)
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

# GS register addresses (A+D mode)
AD_TEX0_1    = 0x06
AD_TEX0_2    = 0x07
AD_XYOFFSET_1 = 0x18
AD_XYOFFSET_2 = 0x19
AD_FRAME_1   = 0x4C
AD_FRAME_2   = 0x4D
AD_BITBLTBUF  = 0x50
AD_TRXPOS     = 0x51
AD_TRXREG     = 0x52
AD_TRXDIR     = 0x53

PSM_NAMES = {0: 'PSMCT32', 1: 'PSMCT24', 2: 'PSMCT16', 0x13: 'PSMT8',
             0x14: 'PSMT4', 0x24: 'PSMT8H', 0x2C: 'PSMT4HL', 0x36: 'PSMT4HH'}

# Known chargen stat label Y positions
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
    """Parse FRAME register value.
    FBP (bits 0-8): Frame buffer base pointer / 2048
    FBW (bits 16-21): Frame buffer width / 64
    PSM (bits 24-29): Pixel storage mode
    FBMSK (bits 32-63): Frame buffer write mask
    """
    return {
        'fbp': val64 & 0x1FF,           # in units of 2048 (32*64)
        'fbp_addr': (val64 & 0x1FF) * 32,  # actual VRAM word address (block address)
        'fbw': (val64 >> 16) & 0x3F,
        'psm': (val64 >> 24) & 0x3F,
        'fbmsk': (val64 >> 32) & 0xFFFFFFFF,
        'raw': val64,
    }


def parse_bitbltbuf(val64):
    """Parse BITBLTBUF register (GS VRAM transfer).
    SBP (bits 0-13): Source base pointer / 64
    SBW (bits 16-21): Source width / 64
    SPSM (bits 24-29): Source pixel format
    DBP (bits 32-45): Dest base pointer / 64
    DBW (bits 48-53): Dest width / 64
    DPSM (bits 56-61): Dest pixel format
    """
    return {
        'sbp': val64 & 0x3FFF,
        'sbw': (val64 >> 16) & 0x3F,
        'spsm': (val64 >> 24) & 0x3F,
        'dbp': (val64 >> 32) & 0x3FFF,
        'dbw': (val64 >> 48) & 0x3F,
        'dpsm': (val64 >> 56) & 0x3F,
        'raw': val64,
    }


def parse_trxreg(val64):
    """Parse TRXREG: transfer width (0-11), height (32-43)."""
    return {
        'rrw': val64 & 0xFFF,
        'rrh': (val64 >> 32) & 0xFFF,
    }


def parse_trxpos(val64):
    """Parse TRXPOS: source/dest X,Y positions."""
    return {
        'ssax': val64 & 0x7FF,
        'ssay': (val64 >> 16) & 0x7FF,
        'dsax': (val64 >> 32) & 0x7FF,
        'dsay': (val64 >> 48) & 0x7FF,
        'dir': (val64 >> 59) & 0x3,
    }


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
            pos += 6 + size
            steps += 1
        elif t == 1:
            pos += 2; steps += 1
        elif t == 2:
            if pos + 5 > len(data): return steps
            sz = struct.unpack_from('<I', data, pos + 1)[0]
            if sz > 10_000_000: return steps
            pos += 5 + sz; steps += 1
        elif t == 3:
            pos += 2; steps += 1
        else:
            return steps
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

    if best_cl < 10:
        print(f"  WARNING: No valid packet chain found (best={best_cl} steps)")
        return 0, len(data)

    lo = max(best_off - 10000, 0)
    final_off = best_off
    final_cl = best_cl
    for off in range(lo, best_off + 1):
        cl = try_parse_chain(data, off, 100)
        if cl > final_cl:
            final_cl = cl
            final_off = off

    print(f"  Packet stream starts at offset {final_off} (0x{final_off:X}), chain={final_cl}")
    return final_off, len(data)


class GSDumpAnalyzer:
    def __init__(self):
        self.current_tex0 = None
        self.current_frame = None
        self.current_xyoffset = (0, 0)
        self.draws_319f = []          # draws using TEX0.TBP0=0x319F
        self.frame_writes_319f = []   # FRAME register writes where FBP maps to 0x319F
        self.all_frame_writes = []    # ALL FRAME writes (for context)
        self.bitblt_319f = []         # BITBLTBUF transfers involving 0x319F
        self.all_bitblt = []          # ALL BITBLTBUF for context
        self.all_tex0_values = {}     # all unique TEX0.TBP0 seen
        self.xyoffsets = set()
        self.draw_order = []          # (type, data) tuples in order: 'frame', 'tex0', 'draw', 'bitblt'
        # Track renders-to-0x319F context
        self.rendering_to_319f = False
        self.draws_while_319f_target = []  # draws happening while FRAME targets 0x319F area
        self.pending_bitblt = {}  # track BITBLTBUF/TRXPOS/TRXREG state

    def process_ad_write(self, addr, data64, packet_idx):
        """Process an A+D register write."""
        if addr in (AD_TEX0_1, AD_TEX0_2):
            self.current_tex0 = parse_tex0(data64)
            tbp0 = self.current_tex0['tbp0']
            if tbp0 not in self.all_tex0_values:
                self.all_tex0_values[tbp0] = self.current_tex0

        elif addr in (AD_FRAME_1, AD_FRAME_2):
            frame = parse_frame(data64)
            self.current_frame = frame
            ctx = 1 if addr == AD_FRAME_1 else 2
            self.all_frame_writes.append((frame, ctx, packet_idx))

            # Check if FBP maps to or near 0x319F
            # FBP is in 2048-word (32-block) units. TBP0 is in 256-byte block units.
            # FBP * 32 = TBP0 equivalent
            fbp_as_tbp0 = frame['fbp_addr']
            if fbp_as_tbp0 == TARGET_TBP0:
                self.frame_writes_319f.append((frame, ctx, packet_idx))
                self.rendering_to_319f = True
                self.draw_order.append(('frame_319f', frame, packet_idx))
            else:
                if self.rendering_to_319f:
                    self.rendering_to_319f = False
                    self.draw_order.append(('frame_other', frame, packet_idx))

        elif addr in (AD_XYOFFSET_1, AD_XYOFFSET_2):
            ofx = (data64 & 0xFFFF) / 16.0
            ofy = ((data64 >> 32) & 0xFFFF) / 16.0
            self.current_xyoffset = (ofx, ofy)
            self.xyoffsets.add((ofx, ofy))

        elif addr == AD_BITBLTBUF:
            self.pending_bitblt['buf'] = parse_bitbltbuf(data64)
        elif addr == AD_TRXPOS:
            self.pending_bitblt['pos'] = parse_trxpos(data64)
        elif addr == AD_TRXREG:
            self.pending_bitblt['reg'] = parse_trxreg(data64)
        elif addr == AD_TRXDIR:
            direction = data64 & 0x3
            transfer = {
                'dir': direction,
                'buf': self.pending_bitblt.get('buf'),
                'pos': self.pending_bitblt.get('pos'),
                'reg': self.pending_bitblt.get('reg'),
                'packet_idx': packet_idx,
            }
            self.all_bitblt.append(transfer)
            # Check if this transfer involves 0x319F
            buf = transfer['buf']
            if buf:
                if buf['sbp'] == TARGET_TBP0 or buf['dbp'] == TARGET_TBP0:
                    self.bitblt_319f.append(transfer)
            self.pending_bitblt = {}

    def add_draw(self, tex0, uvs, xys_tl, xys_br, rgbaq, packet_idx):
        draw = {
            'tex0': dict(tex0),
            'uvs': uvs,
            'xys_tl': xys_tl,
            'xys_br': xys_br,
            'rgbaq': rgbaq,
            'xyoffset': self.current_xyoffset,
            'packet_idx': packet_idx,
        }
        if tex0['tbp0'] == TARGET_TBP0:
            self.draws_319f.append(draw)
            self.draw_order.append(('draw_319f', draw, packet_idx))

        if self.rendering_to_319f:
            self.draws_while_319f_target.append(draw)


def parse_packet_stream(data, seg_start, seg_end):
    """Parse the entire packet stream, tracking all state."""
    analyzer = GSDumpAnalyzer()
    pos = seg_start
    packet_idx = 0

    while pos < seg_end:
        t = data[pos]
        if t == 0:  # Transfer
            if pos + 6 > seg_end:
                break
            path = data[pos + 1]
            size = struct.unpack_from('<I', data, pos + 2)[0]
            if path not in (1, 2, 3) or size > 10_000_000:
                pos += 6 + size
                packet_idx += 1
                continue

            gif = data[pos + 6: pos + 6 + size]
            parse_gif_packet(gif, analyzer, packet_idx)

            pos += 6 + size
            packet_idx += 1
        elif t in (1, 3):
            pos += 2
            packet_idx += 1
        elif t == 2:
            if pos + 5 > seg_end:
                break
            sz = struct.unpack_from('<I', data, pos + 1)[0]
            pos += 5 + sz
            packet_idx += 1
        else:
            pos += 1
            packet_idx += 1

    return analyzer


def parse_gif_packet(gif, analyzer, packet_idx):
    """Parse a GIF packet, updating analyzer state and collecting draws."""
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
                    if gp + 16 > len(gif):
                        return
                    qw_lo = struct.unpack_from('<Q', gif, gp)[0]
                    qw_hi = struct.unpack_from('<Q', gif, gp + 8)[0]
                    gp += 16
                    if reg_id == REG_AD:
                        ad = qw_hi & 0xFF
                        analyzer.process_ad_write(ad, qw_lo, packet_idx)

        elif flg == 1:  # REGLIST
            regs = [(tag_hi >> (i * 4)) & 0xF for i in range(nreg)]
            has_uv = REG_UV in regs
            has_xy = (REG_XYZ2 in regs or REG_XYZF2 in regs or REG_XYZ3 in regs)
            local_tex0 = analyzer.current_tex0

            if has_uv and has_xy and local_tex0:
                uvs = []
                xys_tl = []
                xys_br = []
                rgbaq = None

                for li in range(nloop):
                    for reg_id in regs:
                        if gp + 8 > len(gif):
                            break
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
                    analyzer.add_draw(local_tex0, uvs, xys_tl, xys_br, rgbaq, packet_idx)
            else:
                tb = nloop * nreg * 8
                if tb % 16: tb += 16 - (tb % 16)
                gp += tb

        elif flg == 2:  # IMAGE
            gp += nloop * 16

        if eop:
            break


def gs_to_screen(gs_x, gs_y, xyoffset):
    return gs_x - xyoffset[0], gs_y - xyoffset[1]


def match_stat_label(sy):
    for target_y, label in STAT_LABELS.items():
        if abs(sy - target_y) < Y_TOLERANCE:
            return label
    return None


def main():
    print("=" * 130)
    print("GS DUMP ANALYSIS: TBP0=0x319F")
    print("=" * 130)

    print("\nDecompressing GS dump...")
    data = decompress_gs_dump(GS_DUMP_PATH)
    print(f"Decompressed: {len(data):,} bytes")

    print("\nFinding packet stream...")
    seg_start, seg_end = find_packet_stream(data)

    print("\nParsing packet stream (tracking TEX0, FRAME, BITBLTBUF, draws)...")
    analyzer = parse_packet_stream(data, seg_start, seg_end)

    # ===== SECTION 1: XYOFFSET =====
    print(f"\n{'=' * 130}")
    print("SECTION 1: XYOFFSET VALUES")
    print(f"{'=' * 130}")
    for ofx, ofy in sorted(analyzer.xyoffsets):
        print(f"  OFX={ofx:.1f}, OFY={ofy:.1f}")

    # ===== SECTION 2: ALL TEX0 VALUES =====
    print(f"\n{'=' * 130}")
    print(f"SECTION 2: ALL UNIQUE TEX0 VALUES ({len(analyzer.all_tex0_values)})")
    print(f"{'=' * 130}")
    for tbp0 in sorted(analyzer.all_tex0_values.keys()):
        t = analyzer.all_tex0_values[tbp0]
        psm_name = PSM_NAMES.get(t['psm'], f"0x{t['psm']:02X}")
        marker = " <<<< TARGET" if tbp0 == TARGET_TBP0 else ""
        print(f"  TBP0=0x{tbp0:04X}  TBW={t['tbw']:>2}  PSM={psm_name:<8}  "
              f"size={t['tw']:>4}x{t['th']:<4}{marker}")

    # ===== SECTION 3: FRAME REGISTER WRITES =====
    print(f"\n{'=' * 130}")
    print(f"SECTION 3: FRAME REGISTER WRITES (FBP -> TBP0 mapping)")
    print(f"{'=' * 130}")
    print(f"\nTotal FRAME writes: {len(analyzer.all_frame_writes)}")

    # Show unique FRAME values
    unique_frames = {}
    for frame, ctx, pidx in analyzer.all_frame_writes:
        key = frame['raw']
        if key not in unique_frames:
            unique_frames[key] = (frame, ctx, pidx)

    print(f"Unique FRAME values: {len(unique_frames)}")
    print(f"\n  {'FBP':>6}  {'FBP*32':>8}  {'FBP*32 hex':>10}  {'FBW':>4}  {'PSM':>8}  {'FBMSK':>10}  {'Ctx':>4}  {'Match?'}")
    print("  " + "-" * 80)
    for raw in sorted(unique_frames.keys()):
        frame, ctx, pidx = unique_frames[raw]
        psm_name = PSM_NAMES.get(frame['psm'], f"0x{frame['psm']:02X}")
        match = ""
        if frame['fbp_addr'] == TARGET_TBP0:
            match = " <<<< MATCH: RENDER TARGET!"
        # Also check nearby values
        elif abs(frame['fbp_addr'] - TARGET_TBP0) < 64:
            match = f" (near 0x319F, diff={frame['fbp_addr'] - TARGET_TBP0})"
        print(f"  {frame['fbp']:>6}  {frame['fbp_addr']:>8}  0x{frame['fbp_addr']:04X}  "
              f"{frame['fbw']:>4}  {psm_name:>8}  0x{frame['fbmsk']:08X}  {ctx:>4}  {match}")

    # Specific check for 0x319F
    print(f"\n  FRAME writes with FBP*32 = 0x{TARGET_TBP0:04X}: {len(analyzer.frame_writes_319f)}")
    if analyzer.frame_writes_319f:
        print("  >>> 0x319F IS A RENDER TARGET <<<")
        for frame, ctx, pidx in analyzer.frame_writes_319f:
            psm_name = PSM_NAMES.get(frame['psm'], f"0x{frame['psm']:02X}")
            print(f"    FBP={frame['fbp']} FBP*32=0x{frame['fbp_addr']:04X} FBW={frame['fbw']} "
                  f"PSM={psm_name} FBMSK=0x{frame['fbmsk']:08X} ctx={ctx} packet#{pidx}")
    else:
        print("  >>> 0x319F is NOT a render target (no FRAME writes match) <<<")
        # Check if any frame writes are close
        close = [(f, c, p) for f, c, p in analyzer.all_frame_writes
                 if abs(f['fbp_addr'] - TARGET_TBP0) < 256]
        if close:
            print(f"  Nearest FRAME writes to 0x319F:")
            seen_raw = set()
            for f, c, p in close:
                if f['raw'] not in seen_raw:
                    seen_raw.add(f['raw'])
                    print(f"    FBP*32=0x{f['fbp_addr']:04X} (diff={f['fbp_addr']-TARGET_TBP0:+d})")

    # ===== SECTION 4: BITBLTBUF TRANSFERS =====
    print(f"\n{'=' * 130}")
    print(f"SECTION 4: BITBLTBUF TRANSFERS INVOLVING 0x{TARGET_TBP0:04X}")
    print(f"{'=' * 130}")
    print(f"\nTotal BITBLTBUF transfers: {len(analyzer.all_bitblt)}")
    print(f"Transfers involving 0x{TARGET_TBP0:04X}: {len(analyzer.bitblt_319f)}")

    if analyzer.bitblt_319f:
        for xfer in analyzer.bitblt_319f:
            buf = xfer['buf']
            pos = xfer.get('pos', {})
            reg = xfer.get('reg', {})
            direction = xfer['dir']
            dir_names = {0: 'host->local (upload)', 1: 'local->host (download)', 2: 'local->local (copy)'}
            dir_str = dir_names.get(direction, f'unknown({direction})')

            psm_s = PSM_NAMES.get(buf['spsm'], f"0x{buf['spsm']:02X}") if buf else "?"
            psm_d = PSM_NAMES.get(buf['dpsm'], f"0x{buf['dpsm']:02X}") if buf else "?"

            print(f"\n  Direction: {dir_str}")
            if buf:
                print(f"  Source: SBP=0x{buf['sbp']:04X} SBW={buf['sbw']} SPSM={psm_s}")
                print(f"  Dest:   DBP=0x{buf['dbp']:04X} DBW={buf['dbw']} DPSM={psm_d}")
            if pos:
                print(f"  SrcPos: ({pos['ssax']},{pos['ssay']})  DstPos: ({pos['dsax']},{pos['dsay']})")
            if reg:
                print(f"  Size:   {reg['rrw']}x{reg['rrh']}")
    else:
        # Check for transfers near 0x319F
        print("\n  No exact matches. Checking for transfers near 0x319F...")
        close_xfers = []
        for xfer in analyzer.all_bitblt:
            buf = xfer.get('buf')
            if buf:
                if abs(buf['sbp'] - TARGET_TBP0) < 256 or abs(buf['dbp'] - TARGET_TBP0) < 256:
                    close_xfers.append(xfer)
        if close_xfers:
            for xfer in close_xfers[:10]:
                buf = xfer['buf']
                print(f"    SBP=0x{buf['sbp']:04X} DBP=0x{buf['dbp']:04X} dir={xfer['dir']}")
        else:
            print("  No transfers near 0x319F found either.")

    # ===== SECTION 5: DRAWS USING TEX0.TBP0=0x319F =====
    print(f"\n{'=' * 130}")
    print(f"SECTION 5: ALL DRAWS USING TEX0.TBP0=0x{TARGET_TBP0:04X}")
    print(f"{'=' * 130}")
    print(f"\nTotal draws with TBP0=0x{TARGET_TBP0:04X}: {len(analyzer.draws_319f)}")

    if analyzer.draws_319f:
        # Get texture info
        t = analyzer.draws_319f[0]['tex0']
        psm_name = PSM_NAMES.get(t['psm'], f"0x{t['psm']:02X}")
        print(f"Texture: TBP0=0x{t['tbp0']:04X} TBW={t['tbw']} PSM={psm_name} "
              f"size={t['tw']}x{t['th']} raw=0x{t['raw']:016X}")

        # Sort by screen Y position
        draws_sorted = sorted(analyzer.draws_319f, key=lambda d: (
            d['xys_tl'][0][1] if d['xys_tl'] else (d['xys_br'][0][1] if d['xys_br'] else 0),
            d['xys_tl'][0][0] if d['xys_tl'] else (d['xys_br'][0][0] if d['xys_br'] else 0),
        ))

        print(f"\n{'#':>3}  {'UV TL':>14}  {'UV BR':>14}  {'UV Size':>8}  "
              f"{'Screen TL':>14}  {'Screen BR':>14}  {'Scr Size':>10}  {'Label':>8}  {'Pkt#':>6}")
        print("-" * 120)

        for i, d in enumerate(draws_sorted):
            uvs = d['uvs']
            xyoff = d['xyoffset']

            if len(uvs) >= 2:
                u_tl, v_tl = uvs[0]
                u_br, v_br = uvs[1]
                uv_w = u_br - u_tl
                uv_h = v_br - v_tl
            elif len(uvs) == 1:
                u_tl, v_tl = uvs[0]
                u_br, v_br = u_tl, v_tl
                uv_w = uv_h = 0
            else:
                continue

            scr_tl_str = "N/A"
            scr_br_str = "N/A"
            scr_sz_str = "N/A"
            sx_tl = sy_tl = None

            if d['xys_tl']:
                sx_tl, sy_tl = gs_to_screen(*d['xys_tl'][0], xyoff)
                scr_tl_str = f"({sx_tl:.0f},{sy_tl:.0f})"

            if d['xys_br']:
                sx_br, sy_br = gs_to_screen(*d['xys_br'][0], xyoff)
                scr_br_str = f"({sx_br:.0f},{sy_br:.0f})"
                if d['xys_tl']:
                    sw = sx_br - sx_tl
                    sh = sy_br - sy_tl
                    scr_sz_str = f"{sw:.0f}x{sh:.0f}"

            label = ""
            if sy_tl is not None:
                m = match_stat_label(sy_tl)
                if m:
                    label = f"<- {m}"

            print(f"{i:>3}  ({u_tl:6.1f},{v_tl:5.1f})  ({u_br:6.1f},{v_br:5.1f})  "
                  f"{uv_w:3.0f}x{uv_h:<3.0f}  {scr_tl_str:>14}  {scr_br_str:>14}  "
                  f"{scr_sz_str:>10}  {label:>8}  {d['packet_idx']:>6}")

    # ===== SECTION 6: DRAWS WHILE FRAME TARGETS 0x319F =====
    print(f"\n{'=' * 130}")
    print(f"SECTION 6: DRAWS RENDERED INTO 0x{TARGET_TBP0:04X} (while FRAME.FBP targets it)")
    print(f"{'=' * 130}")
    print(f"\nDraws rendered while FRAME targets 0x319F: {len(analyzer.draws_while_319f_target)}")

    if analyzer.draws_while_319f_target:
        # These are the draws that COMPOSE the render target content
        print("These draws reveal what glyphs/textures are composited into the 0x319F buffer.")

        # Group by source TEX0
        src_tex0_groups = {}
        for d in analyzer.draws_while_319f_target:
            tbp0 = d['tex0']['tbp0']
            if tbp0 not in src_tex0_groups:
                src_tex0_groups[tbp0] = []
            src_tex0_groups[tbp0].append(d)

        print(f"\nSource textures used while rendering to 0x319F:")
        for tbp0 in sorted(src_tex0_groups.keys()):
            draws = src_tex0_groups[tbp0]
            t = draws[0]['tex0']
            psm_name = PSM_NAMES.get(t['psm'], f"0x{t['psm']:02X}")
            print(f"  TBP0=0x{tbp0:04X} TBW={t['tbw']} PSM={psm_name} "
                  f"size={t['tw']}x{t['th']} -- {len(draws)} draws")

        # Print all draws with detail
        draws_sorted = sorted(analyzer.draws_while_319f_target, key=lambda d: (
            d['xys_tl'][0][1] if d['xys_tl'] else 0,
            d['xys_tl'][0][0] if d['xys_tl'] else 0,
        ))

        print(f"\n{'#':>3}  {'SrcTBP0':>8}  {'UV TL':>14}  {'UV BR':>14}  {'UV Size':>8}  "
              f"{'RT pos TL':>14}  {'RT pos BR':>14}  {'RT Size':>10}  {'Pkt#':>6}")
        print("-" * 120)

        for i, d in enumerate(draws_sorted):
            uvs = d['uvs']
            xyoff = d['xyoffset']

            if len(uvs) >= 2:
                u_tl, v_tl = uvs[0]
                u_br, v_br = uvs[1]
                uv_w = u_br - u_tl
                uv_h = v_br - v_tl
            else:
                continue

            # When rendering to a render target, screen positions are relative to the RT
            rt_tl = "N/A"
            rt_br = "N/A"
            rt_sz = "N/A"
            if d['xys_tl']:
                rx, ry = gs_to_screen(*d['xys_tl'][0], xyoff)
                rt_tl = f"({rx:.0f},{ry:.0f})"
                if d['xys_br']:
                    rx2, ry2 = gs_to_screen(*d['xys_br'][0], xyoff)
                    rt_br = f"({rx2:.0f},{ry2:.0f})"
                    rt_sz = f"{rx2-rx:.0f}x{ry2-ry:.0f}"

            print(f"{i:>3}  0x{d['tex0']['tbp0']:04X}  ({u_tl:6.1f},{v_tl:5.1f})  ({u_br:6.1f},{v_br:5.1f})  "
                  f"{uv_w:3.0f}x{uv_h:<3.0f}  {rt_tl:>14}  {rt_br:>14}  {rt_sz:>10}  {d['packet_idx']:>6}")

    # ===== SECTION 7: DRAW ORDER ANALYSIS =====
    print(f"\n{'=' * 130}")
    print(f"SECTION 7: DRAW ORDER (FRAME changes and 0x319F draws in sequence)")
    print(f"{'=' * 130}")
    for event_type, event_data, pidx in analyzer.draw_order:
        if event_type == 'frame_319f':
            frame = event_data
            psm_name = PSM_NAMES.get(frame['psm'], f"0x{frame['psm']:02X}")
            print(f"  [pkt {pidx:>5}] FRAME -> 0x{frame['fbp_addr']:04X} "
                  f"(FBW={frame['fbw']} PSM={psm_name} MASK=0x{frame['fbmsk']:08X}) "
                  f"*** RENDERING TO 0x319F ***")
        elif event_type == 'frame_other':
            frame = event_data
            print(f"  [pkt {pidx:>5}] FRAME -> 0x{frame['fbp_addr']:04X} "
                  f"(stopped rendering to 0x319F)")
        elif event_type == 'draw_319f':
            d = event_data
            uvs = d['uvs']
            xyoff = d['xyoffset']
            if len(uvs) >= 2:
                u_tl, v_tl = uvs[0]
                u_br, v_br = uvs[1]
            else:
                continue
            scr = "N/A"
            label = ""
            if d['xys_tl']:
                sx, sy = gs_to_screen(*d['xys_tl'][0], xyoff)
                scr = f"({sx:.0f},{sy:.0f})"
                m = match_stat_label(sy)
                if m:
                    label = f" <- {m}"
            print(f"  [pkt {pidx:>5}] DRAW from 0x319F: UV=({u_tl:.1f},{v_tl:.1f})-({u_br:.1f},{v_br:.1f}) "
                  f"screen={scr}{label}")

    # ===== SECTION 8: CONCLUSION =====
    print(f"\n{'=' * 130}")
    print(f"SECTION 8: CONCLUSION")
    print(f"{'=' * 130}")

    is_render_target = len(analyzer.frame_writes_319f) > 0
    has_bitblt = len(analyzer.bitblt_319f) > 0
    has_draws_from = len(analyzer.draws_319f) > 0
    has_draws_into = len(analyzer.draws_while_319f_target) > 0

    print(f"\n  TBP0 = 0x{TARGET_TBP0:04X}")
    print(f"  FRAME writes targeting 0x319F: {len(analyzer.frame_writes_319f)}")
    print(f"  BITBLTBUF transfers involving 0x319F: {len(analyzer.bitblt_319f)}")
    print(f"  Draws FROM 0x319F (used as texture): {len(analyzer.draws_319f)}")
    print(f"  Draws INTO 0x319F (rendered while FRAME targets it): {len(analyzer.draws_while_319f_target)}")

    if is_render_target and has_draws_into:
        print(f"\n  VERDICT: 0x319F is a RENDER TARGET.")
        print(f"  The game composites glyph draws into this buffer, then later")
        print(f"  reads it as a texture (TEX0.TBP0=0x319F) to draw stat labels.")
        print(f"  ")
        print(f"  To change stat labels, you need to change the GLYPH IDs that")
        print(f"  feed the composition step (R39/EXE glyph streams), NOT the texture data.")
    elif is_render_target and not has_draws_into:
        print(f"\n  VERDICT: 0x319F is a RENDER TARGET (FRAME writes found)")
        print(f"  but no draws were captured while it was the target.")
        print(f"  The composition may happen before the GS dump capture window.")
    elif has_bitblt:
        print(f"\n  VERDICT: 0x319F receives data via BITBLTBUF transfer (uploaded from CPU/disc).")
    else:
        print(f"\n  VERDICT: 0x319F appears to be a REGULAR TEXTURE loaded from disc/CPU.")
        print(f"  No FRAME or BITBLTBUF writes target this address.")


if __name__ == '__main__':
    main()
