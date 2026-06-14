import json, sys, io, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Load glyph table
table = json.load(open("data/english_glyph_table.json", encoding="utf-8"))

def encode_text(english_text, max_chars_per_line=16, max_lines_per_page=3):
    """Encode English text to BE uint16 glyph stream with word wrapping.

    max_chars_per_line is a SAFETY HARD-WRAP fallback. The default of 16 fits
    the narrowest (centered-narration) frame. Callers that have authored
    explicit ' / ' breaks should pass each pre-broken segment in separately so
    that segments already within the fallback are NOT force-rewrapped; only a
    segment that genuinely exceeds the fallback is hard-wrapped here.
    """
    words = english_text.replace("\n", " ").split()
    
    glyphs = []
    line_chars = 0
    lines_on_page = 1
    
    for wi, word in enumerate(words):
        word_len = len(word)
        
        # Check if word fits on current line
        if line_chars > 0 and line_chars + 1 + word_len > max_chars_per_line:
            # Need line break
            glyphs.append(0xFFFE)  # line break
            lines_on_page += 1
            line_chars = 0
            
            if lines_on_page > max_lines_per_page:
                # Page break (FFD2 after FFFE)
                glyphs.append(0xFFD2)
                lines_on_page = 1
        
        # Add space before word (except at line start)
        if line_chars > 0:
            glyphs.append(table.get(" ", 1))
            line_chars += 1
        
        # Encode each character
        for char in word:
            glyph = table.get(char)
            if glyph is None:
                # Try case-insensitive
                glyph = table.get(char.lower()) or table.get(char.upper())
            if glyph is None:
                glyph = table.get("?", 31)  # fallback to ?
            glyphs.append(glyph)
            line_chars += 1
    
    return glyphs

def encode_to_bytes(glyphs):
    """Convert glyph list to BE uint16 byte stream."""
    return b"".join(struct.pack(">H", g) for g in glyphs)

if __name__ == "__main__":
    # Test
    test = "Welcome to Vigger Shop! What can I do for you today?"
    glyphs = encode_text(test)
    decoded = ""
    for g in glyphs:
        if g == 0xFFFE: decoded += " | "
        elif g == 0xFFD2: decoded += " [PAGE] "
        else:
            for c, idx in table.items():
                if idx == g:
                    decoded += c
                    break
    print(f"Input:  {test}")
    print(f"Glyphs: {glyphs}")
    print(f"Verify: {decoded}")
    print(f"Bytes:  {len(encode_to_bytes(glyphs))} bytes")
