import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Build English character -> glyph index mapping
# Reusing existing slots where possible, repurposing hiragana slots for uppercase
table = {}

# Space
table[" "] = 1

# Lowercase a-z at existing slots 33-58
for i, c in enumerate("abcdefghijklmnopqrstuvwxyz"):
    table[c] = 33 + i

# Digits 0-9 at existing fullwidth slots 16-25
for i in range(10):
    table[str(i)] = 16 + i

# Uppercase A-Z repurposing hiragana slots 112-137
for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    table[c] = 112 + i

# Punctuation - reuse existing ASCII glyph slots from EXE table
table["!"] = 5
table['"'] = 6
table["#"] = 7
table["$"] = 8
table["%"] = 9
table["&"] = 10
table["'"] = 13
table["("] = 14
table[")"] = 15
table["+"] = 27  # repurpose
table[","] = 28
table["-"] = 29
table["."] = 30
table["/"] = 26
table[":"] = 34 + 26  # repurpose slot after z = 60
table[";"] = 61
table["<"] = 37 + 26  # = 63... actually let me use simpler assignments
table["?"] = 31  # was mapped as ? in the game
table["@"] = 32

# Simpler: map remaining punctuation to available slots
# Slots 59-97 are mostly available (after a-z ends at 58)
table[":"] = 59
table[";"] = 60
table["<"] = 61
table["="] = 62  # was 、 in Japanese but we're replacing
table[">"] = 63  # was 。 in Japanese
table["["] = 64
table["]"] = 65
table["_"] = 66
table["{"] = 67
table["}"] = 68
table["~"] = 69
table["*"] = 70
table["\\"] = 71

# Line break marker (for reference, not an actual glyph)
# FFFE = line break, FFFF = message end

with open("data/english_glyph_table.json", "w", encoding="utf-8") as f:
    json.dump(table, f, ensure_ascii=False, indent=2)

print(f"English glyph table: {len(table)} characters mapped")
for c in sorted(table.keys()):
    print(f"  '{c}' -> glyph {table[c]}")
