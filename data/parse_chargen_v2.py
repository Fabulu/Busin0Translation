"""Parse R1196-R1212 - find messages containing HP, MP, numbers, and stat-related ASCII text."""
import struct
import os

RAW_DIR = "C:/Programmieren/wizardrytranslation/extracted/packdata_raw"
OUTPUT = "C:/Programmieren/wizardrytranslation/data/chargen_resource_dump.txt"

def decode_glyph(gid):
    if 0 <= gid <= 94:
        return chr(gid + 0x20)
    else:
        return f"[{gid}]"

def decode_message(glyphs):
    return ''.join(decode_glyph(g) for g in glyphs)

def parse_sec2_messages(sec2_data):
    messages = []
    n_words = len(sec2_data) // 2
    current = []
    for i in range(n_words):
        w = struct.unpack_from(">H", sec2_data, i * 2)[0]
        if w == 0xFFFF:
            messages.append(current)
            current = []
        else:
            current.append(w)
    if current:
        messages.append(current)
    return messages

def has_ascii_text(msg, min_consecutive=2):
    """Check if message has consecutive ASCII characters (actual text, not just punctuation)."""
    consecutive = 0
    max_consecutive = 0
    for g in msg:
        if 0 <= g <= 94:
            ch = chr(g + 0x20)
            if ch.isalnum():
                consecutive += 1
                max_consecutive = max(max_consecutive, consecutive)
            else:
                consecutive = 0
        else:
            consecutive = 0
    return max_consecutive >= min_consecutive

def extract_ascii_words(msg):
    """Extract ASCII words from message."""
    text = decode_message(msg)
    words = []
    current = []
    for ch in text:
        if ch.isalnum() or ch == '/':
            current.append(ch)
        else:
            if current:
                w = ''.join(current)
                if len(w) >= 2 and any(c.isalpha() for c in w):
                    words.append(w)
                current = []
    if current:
        w = ''.join(current)
        if len(w) >= 2 and any(c.isalpha() for c in w):
            words.append(w)
    return words

with open(OUTPUT, 'w', encoding='utf-8') as out:
    out.write("=" * 80 + "\n")
    out.write("CHARGEN STATE MSG RESOURCES: R1196-R1212\n")
    out.write("Focus: Messages containing ASCII text (stat labels, HP/MP, etc.)\n")
    out.write("=" * 80 + "\n\n")

    for rid in range(1196, 1213):
        fpath = os.path.join(RAW_DIR, f"{rid}_type02.raw")
        with open(fpath, 'rb') as f:
            data = f.read()

        if len(data) < 0x1C:
            continue

        h = struct.unpack_from('<7I', data, 0)
        sec2_size = h[5]
        sec2_off = h[6]

        sec1_start = 0x1C
        sec1_size = sec2_off - sec1_start

        if sec2_off + sec2_size > len(data):
            sec2_size = len(data) - sec2_off

        sec2_data = data[sec2_off:sec2_off + sec2_size]
        messages = parse_sec2_messages(sec2_data)

        out.write(f"\n{'='*80}\n")
        out.write(f"R{rid} -- {len(data)} bytes, {len(messages)} messages\n")
        out.write(f"  sec1={sec1_size}B ({sec1_size//2} words), sec2={sec2_size}B ({sec2_size//2} words)\n")
        out.write(f"{'='*80}\n\n")

        # Find messages with ASCII text
        ascii_msgs = []
        pos = 0
        for mi, msg in enumerate(messages):
            if has_ascii_text(msg, 2):
                words = extract_ascii_words(msg)
                text = decode_message(msg)
                if len(text) > 300:
                    text = text[:300] + "..."
                ascii_msgs.append((mi, pos, msg, text, words))
            pos += len(msg) + 1

        out.write(f"Messages with ASCII text: {len(ascii_msgs)} / {len(messages)}\n\n")

        for mi, word_pos, msg, text, words in ascii_msgs:
            out.write(f"  msg[{mi:4d}] @word {word_pos:5d} ({len(msg):3d} glyphs): "
                      f"ASCII_WORDS={words}\n")
            out.write(f"           text: {text}\n\n")

        # Also show the first 20 messages for context
        out.write(f"\nFirst 20 messages (full dump):\n")
        pos = 0
        for mi, msg in enumerate(messages[:20]):
            text = decode_message(msg)
            if len(text) > 200:
                text = text[:200] + "..."
            ascii_count = sum(1 for g in msg if 0 <= g <= 94)
            kanji_count = sum(1 for g in msg if g > 94 and g < 0xFF00)
            ctrl_count = sum(1 for g in msg if g >= 0xFF00)
            out.write(f"  msg[{mi:3d}] @w{pos:5d} ({len(msg):3d}g a={ascii_count} k={kanji_count} c={ctrl_count}): {text}\n")
            pos += len(msg) + 1
        out.write("\n")

    # Key observations
    out.write("\n" + "=" * 80 + "\n")
    out.write("KEY OBSERVATIONS\n")
    out.write("=" * 80 + "\n\n")
    out.write("1. ALL resources share the same msg[0]: [887]...[1040][191][127]_ (22 glyphs)\n")
    out.write("   This is likely a common chargen intro/prompt message.\n\n")
    out.write("2. msg[1] in R1196-R1197 is 25 glyphs, but in R1203+ it's 193 glyphs.\n")
    out.write("   The 193-glyph msg[1] contains numbered options (1-9+) and is a menu/list.\n\n")
    out.write("3. HP/MP appear as literal ASCII in a fixed phrase:\n")
    out.write("   [259]}[211][268][136]HP{MP[158][670][1241][123][127]!\n")
    out.write("   This is dialogue text mentioning HP and MP, NOT stat labels.\n\n")
    out.write("4. ON/OFF appear in R1203-R1212 (not R1196-R1202) as toggle options:\n")
    out.write("   [234][254]}[156]ON/OFF[133][123][127]_\n")
    out.write("   These are likely in-game toggle confirmations.\n\n")
    out.write("5. Gold amounts (1000G, 2000G, 5000G, etc.) appear in shop/purchase contexts.\n\n")
    out.write("6. B2-B10 references appear in R1204-R1212 respectively:\n")
    out.write("   [273][268][239]}[466][377]...[298][277][64257][65505]B##[65504][64256]\n")
    out.write("   These are floor/basement references for dungeon exploration.\n\n")
    out.write("7. 0123456789- appears as a number rendering template (11 glyphs).\n")
    out.write("   Used for stat/number display formatting.\n\n")
    out.write("8. These resources are NOT chargen state resources for character creation.\n")
    out.write("   They contain NPC dialogue, shop interactions, dungeon exploration text,\n")
    out.write("   and event scripts. The 'chargen state' hypothesis was incorrect.\n\n")
    out.write("9. The stat labels for character creation are likely in EXE structs or\n")
    out.write("   rendered via R1272 font tile mappings, not in these MSG resources.\n\n")

    # Final summary
    out.write("\n" + "=" * 80 + "\n")
    out.write("SUMMARY\n")
    out.write("=" * 80 + "\n\n")

    for rid in range(1196, 1213):
        fpath = os.path.join(RAW_DIR, f"{rid}_type02.raw")
        with open(fpath, 'rb') as f:
            data = f.read()
        if len(data) < 0x1C:
            continue
        h = struct.unpack_from('<7I', data, 0)
        sec2_data = data[h[6]:h[6] + h[5]]
        messages = parse_sec2_messages(sec2_data)

        # Collect all ASCII words across all messages
        all_words = set()
        for msg in messages:
            all_words.update(extract_ascii_words(msg))

        out.write(f"R{rid}: {len(messages):4d} msgs, ASCII words: {sorted(all_words)}\n")

print("Done!")
