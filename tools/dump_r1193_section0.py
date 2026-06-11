#!/usr/bin/env python3
"""
Dump and parse R1193 Section 0 (intro narration animation script).

Section 0 Format Summary
=========================

R1193 is a type-02 resource with 2 sections:
  - Section 0 (offset 0x20, 4800 bytes): Animation/timing script (this file documents)
  - Section 1 (offset 0x12E0, 702 bytes): Text glyph IDs (BE uint16, FFFF-delimited)

R1194 (ending narration) uses the same format but is entirely even-aligned.

FILE HEADER (LE uint32, 0x00-0x1F):
  0x00: 0x00000000 (zero/magic)
  0x04: section 0 size (LE uint32) -- R1193: 4800
  0x08: section 0 offset (LE uint32) -- always 0x20
  0x0C: 0x00000000
  0x10: 0x00000001 (section count minus 1?)
  0x14: section 1 size (LE uint32) -- R1193: 702
  0x18: section 1 offset (LE uint32) -- R1193: 0x12E0

SECTION 0 SUB-HEADER (BE uint16, 5 words = 10 bytes):
  word[0] = 2 (format version)
  word[1] = 3 (format sub-type)
  word[2] = page/line count (R1193: 32, R1194: 58)
  word[3] = 0 (reserved)
  word[4] = byte offset within sec0 to second pass start marker (0x4D byte)
            R1193: 0x0645=1605, R1194: 0x000C=12

SECTION 0 BODY (ALL BE uint16):
  The body is a stream of opcodes with variable-length arguments.

  R1193 specifically has a 1-BYTE ALIGNMENT SHIFT:
    Bytes 10-295: Even-aligned BE opcodes (pass 1 setup + CHAR_DEFs + timing)
    Bytes 296-356: Binary data table (61 bytes, ODD length)
    Bytes 357 onward: ODD-aligned BE opcodes (animation timeline + pass 2)

  R1194 has no alignment shift (all even-aligned throughout).

DATA TABLE (bytes 296-356 in R1193):
  61-byte binary block between the two aligned sections.
  Contains 4 entries (one per text display slot) with keyframe data.
  The entries contain values like frame counters (0x00FF, 0x01FF, 0x02FF, 0x03FF)
  and timing parameters (0x1400=5120, etc.). Exact format TBD.
  This table does NOT exist in R1194.

OPCODE TABLE:
  All opcodes and params are BE uint16. Signed values use two's complement.

  Scene Setup:
    0x1A           SYNC        Separator/sync point (0 params)
    0x4D msg       MSG         Select section 1 message index (1 param)
    0x63 p         OP_c        Scene config (1 param)
    0x65 p         OP_e        Scene config (1 param)
    0x62 p         OP_b        Scene config (1 param)
    0x4E p1 p2     OP_N        Scene param (2 params)
    0x98 p         OP_98       Scene param (1 param)
    0x99 p         OP_99       Scene param (1 param)
    0x4C p         OP_L        Scene param (1 param)
    0x6C p         OP_l        Scene param (1 param)

  Character Slots (decoration glyphs, NOT narration text):
    0x43 idx gl    CHAR        Define char slot: idx=slot(0-7), gl=glyph_id (2 params)
    0x45 idx d dx dy  SHOW     Show char: idx, delay, dx/dy offsets (4 params)
                               dx=dy=0xFFFF means static (no animation offset)
    0x46 idx p     HIDE        Hide char: idx, param (2 params)
    0x44 idx       OP_D        Deactivate slot (1 param)

  Animation:
    0x61 idx p1 p2 y1 y2  TEXTLINE  Display text line on screen (5 params)
                                     idx=display slot (0-3), y1/y2=Y coordinates (signed)
    0x64 dur p     FADE        Fade effect: duration, param (2 params)
    0x6E p1 p2     SCROLL      Scroll effect (2 params)
    0x49 idx p1 p2 OP_I        Animation property (3 params)
    0x48 idx p1 p2 OP_H        Animation property (3 params)
    0x4B p         OP_K        Keyframe (1 param)
    0x5A p         OP_Z        Animation control (1 param)

  Timing:
    0x10 frames    DELAY       Wait N frames (1 param)
    0x3C frames    WAIT        Wait N frames (1 param)
    0x14 p         OP_14       Timing/keyframe param (1 param)
    0x0E p1 p2     OP_0E       (2 params) -- precedes data table in R1193
    0x0F p1 p2     INIT        Initialization (2 params)
    0x0D p1 p2     OP_0D       (2 params)
    0x0C           OP_0C       (0 params)

  Other:
    0x79 p         OP_y        (1 param)
    0x7A p         OP_z        (1 param)
    0x78           OP_x        (0 params)
    0x4F           OP_O        (0 params, seen in R1194)
    0xFFFF         SENTINEL    Record separator

TEXTLINE ANIMATION PATTERN:
  Each narration page displays text in 3 phases per display slot:
    TEXTLINE idx y1 y2  ->  FADE 16 1   ->  DELAY 1    (fade in, 16 frames)
    TEXTLINE idx y1 y2  ->  FADE 56 60  ->  DELAY 60   (hold, ~1 second)
    TEXTLINE idx y1 y2  ->  FADE 96 60  ->  DELAY 60   (fade out, ~1 second)

  In R1193's shifted section, SCROLL(0x6E) is used instead of FADE(0x64):
    TEXTLINE idx y1 y2  ->  SCROLL 16 1  ->  DELAY 1
    TEXTLINE idx y1 y2  ->  SCROLL 128 60 -> DELAY 60
    TEXTLINE idx y1 y2  ->  SCROLL 128 60 -> DELAY 60

  The idx (0-3) selects one of 4 on-screen text display slots.
  The y1/y2 are signed 16-bit Y-coordinates controlling vertical position.

TRANSLATION IMPACT:
  Section 0 does NOT contain text glyphs (those are in Section 1).
  The build pipeline (build_v9.py Step 5) already handles Section 1 translation.
  Section 0 would only need modification to adjust:
    - Y-coordinates in TEXTLINE opcodes (if English text has different line count)
    - Timing values in FADE/DELAY (if display duration needs changing)
    - CHAR glyph IDs (if decoration glyphs need English equivalents)
"""

import struct
import json
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
os.chdir("C:/Programmieren/wizardrytranslation")

gm = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))


def signed16(v):
    return v - 0x10000 if v >= 0x8000 else v


def parse_opcodes(sec0, start_byte, end_byte, odd_aligned=False, label=""):
    """Parse BE uint16 opcode stream. If odd_aligned, read from odd byte offsets."""
    results = []
    pos = start_byte

    def rw(offset):
        """Read BE uint16 at given byte offset."""
        return struct.unpack_from('>H', sec0, offset)[0]

    while pos < end_byte and pos + 1 < len(sec0):
        w = rw(pos)

        if w == 0x0000:
            pos += 2
            continue
        elif w == 0xFFFF:
            results.append(f"  @{pos:4d} FFFF")
            pos += 2
        elif w == 0x001A:
            results.append(f"  @{pos:4d} SYNC")
            pos += 2
        elif w == 0x004D:
            results.append(f"  @{pos:4d} MSG msg_idx={rw(pos+2)}")
            pos += 4
        elif w == 0x0043:
            idx = rw(pos+2); gl = rw(pos+4)
            ch = gm.get(str(gl), '?')
            results.append(f"  @{pos:4d} CHAR idx={idx} glyph={gl}(0x{gl:04X}) \"{ch}\"")
            pos += 6
        elif w == 0x0045:
            idx = rw(pos+2); d = rw(pos+4); dx = rw(pos+6); dy = rw(pos+8)
            if dx == 0xFFFF and dy == 0xFFFF:
                results.append(f"  @{pos:4d} SHOW idx={idx} delay={d} [static]")
            else:
                results.append(f"  @{pos:4d} SHOW idx={idx} delay={d} offset=({signed16(dx)},{signed16(dy)})")
            pos += 10
        elif w == 0x0046:
            results.append(f"  @{pos:4d} HIDE idx={rw(pos+2)} p={rw(pos+4)}")
            pos += 6
        elif w == 0x0061:
            idx = rw(pos+2); p1 = rw(pos+4); p2 = rw(pos+6)
            y1 = rw(pos+8); y2 = rw(pos+10)
            results.append(f"  @{pos:4d} TEXTLINE idx={idx} p=({p1},{p2}) y=({signed16(y1)},{signed16(y2)})")
            pos += 12
        elif w == 0x0064:
            results.append(f"  @{pos:4d} FADE dur={rw(pos+2)} p2={rw(pos+4)}")
            pos += 6
        elif w == 0x006E:
            results.append(f"  @{pos:4d} SCROLL p1={rw(pos+2)} p2={rw(pos+4)}")
            pos += 6
        elif w == 0x0049:
            results.append(f"  @{pos:4d} OP_I idx={rw(pos+2)} p1={rw(pos+4)} p2={rw(pos+6)}")
            pos += 8
        elif w == 0x0048:
            results.append(f"  @{pos:4d} OP_H idx={rw(pos+2)} p1={rw(pos+4)} p2={rw(pos+6)}")
            pos += 8
        elif w == 0x0010:
            results.append(f"  @{pos:4d} DELAY frames={rw(pos+2)}")
            pos += 4
        elif w == 0x003C:
            results.append(f"  @{pos:4d} WAIT frames={rw(pos+2)}")
            pos += 4
        elif w == 0x000E:
            results.append(f"  @{pos:4d} OP_0E p1={rw(pos+2)} p2={rw(pos+4)}")
            pos += 6
        elif w == 0x000F:
            results.append(f"  @{pos:4d} INIT(0F) p1={rw(pos+2)} p2={rw(pos+4)}")
            pos += 6
        elif w == 0x000D:
            results.append(f"  @{pos:4d} OP_0D p1={rw(pos+2)} p2={rw(pos+4)}")
            pos += 6
        elif w == 0x000C:
            results.append(f"  @{pos:4d} OP_0C")
            pos += 2
        elif w == 0x004E:
            results.append(f"  @{pos:4d} OP_N p1={rw(pos+2)} p2={rw(pos+4)}")
            pos += 6
        elif w in (0x44, 0x4B, 0x4C, 0x63, 0x65, 0x62, 0x5A, 0x6C, 0x79, 0x7A, 0x98, 0x99, 0x14):
            names = {
                0x44: 'D', 0x4B: 'K', 0x4C: 'L', 0x63: 'c', 0x65: 'e',
                0x62: 'b', 0x5A: 'Z', 0x6C: 'l', 0x79: 'y', 0x7A: 'z',
                0x98: '98', 0x99: '99', 0x14: '14'
            }
            results.append(f"  @{pos:4d} OP_{names[w]}(0x{w:02X}) p={rw(pos+2)}")
            pos += 4
        elif w == 0x0078:
            results.append(f"  @{pos:4d} OP_x(0x78)")
            pos += 2
        elif w == 0x004F:
            results.append(f"  @{pos:4d} OP_O(0x4F)")
            pos += 2
        else:
            results.append(f"  @{pos:4d} ??? 0x{w:04X} ({w})")
            pos += 2

    return results, pos


def dump_resource(filepath, name=""):
    """Dump section 0 of a type-02 intro/ending narration resource."""
    data = open(filepath, 'rb').read()

    sec0_size = struct.unpack_from('<I', data, 4)[0]
    sec0_offset = struct.unpack_from('<I', data, 8)[0]
    sec1_size = struct.unpack_from('<I', data, 0x14)[0]
    sec1_offset = struct.unpack_from('<I', data, 0x18)[0]

    print(f"{'='*70}")
    print(f"Resource: {name or filepath}")
    print(f"File size: {len(data)} bytes")
    print(f"Section 0: offset=0x{sec0_offset:X}, size={sec0_size}")
    print(f"Section 1: offset=0x{sec1_offset:X}, size={sec1_size}")

    sec0 = data[sec0_offset:sec0_offset + sec0_size]
    header = [struct.unpack_from('>H', sec0, i*2)[0] for i in range(5)]
    print(f"\nSec0 Sub-Header: version={header[0]} type={header[1]} "
          f"pages={header[2]} reserved={header[3]} pass2_offset=0x{header[4]:04X}({header[4]})")

    # Find active data end
    last_nz = 0
    for i in range(0, len(sec0), 2):
        if struct.unpack_from('>H', sec0, i)[0] != 0:
            last_nz = i
    active_end = last_nz + 2
    print(f"Active data: {active_end} bytes, Padding: {len(sec0) - active_end} bytes")

    # Detect alignment shift: scan for the data table pattern
    # Look for the OP_0E opcode followed by params, then the data table
    shift_byte = None
    for byte_off in range(10, min(400, len(sec0)-5), 2):
        w = struct.unpack_from('>H', sec0, byte_off)[0]
        if w == 0x000E:
            # Check if followed by a data table (large values like 0x0200, 0x1000)
            after = byte_off + 6  # skip opcode + 2 params
            if after + 4 < len(sec0):
                v1 = struct.unpack_from('>H', sec0, after)[0]
                v2 = struct.unpack_from('>H', sec0, after + 2)[0]
                if v1 > 0x100 and v2 > 0x100:
                    # Found data table. Scan for where aligned opcodes resume.
                    # Try odd offsets to find clean H/TEXTLINE opcodes
                    for probe in range(after + 10, min(after + 200, len(sec0) - 3), 2):
                        pw = struct.unpack_from('>H', sec0, probe + 1)[0]  # odd-aligned
                        if pw in (0x0048, 0x0061, 0x0049, 0x004D, 0x001A):
                            shift_byte = probe + 1
                            table_start = after
                            table_end = shift_byte
                            print(f"\n** ALIGNMENT SHIFT detected **")
                            print(f"   Data table: bytes {table_start}-{table_end-1} ({table_end-table_start} bytes)")
                            print(f"   Odd-aligned section starts at byte {shift_byte}")
                            break
                    break

    # Parse even-aligned block (before shift)
    even_end = shift_byte - (shift_byte - 10) if shift_byte else active_end
    if shift_byte:
        # Parse up to the OP_0E that precedes the table
        print(f"\n--- Even-aligned block (bytes 10 to ~{table_start-1}) ---")
        results, _ = parse_opcodes(sec0, 10, table_start, label="even")
        for r in results:
            print(r)

        # Dump data table
        print(f"\n--- Data table (bytes {table_start}-{table_end-1}, {table_end-table_start} bytes) ---")
        for i in range(table_start, table_end, 16):
            end = min(i + 16, table_end)
            hex_str = ' '.join(f'{sec0[j]:02X}' for j in range(i, end))
            print(f"  {i:4d}: {hex_str}")

        # Parse odd-aligned block
        print(f"\n--- Odd-aligned block (bytes {shift_byte} to {active_end}) ---")
        results, _ = parse_opcodes(sec0, shift_byte, active_end, odd_aligned=True, label="odd")
        for r in results:
            print(r)
    else:
        # No shift, parse everything even-aligned
        print(f"\n--- Opcode stream (bytes 10 to {active_end}) ---")
        results, _ = parse_opcodes(sec0, 10, active_end, label="even")
        for r in results:
            print(r)

    # Section 1: decode text
    sec1 = data[sec1_offset:sec1_offset + sec1_size]
    print(f"\n--- Section 1 Text ({sec1_size} bytes) ---")
    pos = 0
    msg_idx = 0
    total_glyphs_in_messages = 0
    while pos < len(sec1) - 1:
        gs = []
        while pos < len(sec1) - 1:
            val = struct.unpack_from('>H', sec1, pos)[0]
            pos += 2
            if val == 0xFFFF:
                break
            gs.append(val)
        if gs:
            text = ''
            for g in gs:
                if g == 0xFFFE:
                    text += ' | '
                elif g >= 0xFFC0:
                    text += f'[{g:04X}]'
                else:
                    ch = gm.get(str(g))
                    text += ch if ch else f'({g})'
            print(f"  M{msg_idx} ({len(gs)} glyphs): {text[:200]}")
            total_glyphs_in_messages += len(gs)
        msg_idx += 1

    # Trailing data
    trailing = []
    while pos < len(sec1) - 1:
        val = struct.unpack_from('>H', sec1, pos)[0]
        pos += 2
        trailing.append(val)
    if trailing:
        text = ''
        for g in trailing:
            if g == 0xFFFE:
                text += ' | '
            elif g >= 0xFFC0:
                text += f'[{g:04X}]'
            else:
                ch = gm.get(str(g))
                text += ch if ch else f'({g})'
        print(f"  Trailing ({len(trailing)} glyphs): {text[:300]}...")

    print(f"\n  Total: {msg_idx} messages + trailing, {total_glyphs_in_messages} message glyphs")


if __name__ == '__main__':
    dump_resource('extracted/packdata_raw/1193_type02.raw', 'R1193 (Intro Narration)')
    print("\n\n")
    dump_resource('extracted/packdata_raw/1194_type02.raw', 'R1194 (Ending Narration)')
