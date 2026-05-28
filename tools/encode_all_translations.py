import json, sys, io, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "tools")
from encode_english_text import encode_text, table

LOG = open("dumps/encoding_log.txt", "w", encoding="utf-8")
def log(msg):
    LOG.write(msg + "\n"); LOG.flush()

# Load all translations
all_translations = []
for f in ["data/translations_items_monsters.json", "data/translations_shop_church.json",
          "data/translations_menus.json", "data/translations_dungeon_story.json"]:
    try:
        data = json.load(open(f, encoding="utf-8"))
        if isinstance(data, list):
            all_translations.extend(data)
        elif isinstance(data, dict):
            for key, val in data.items():
                if isinstance(val, list):
                    all_translations.extend(val)
                elif isinstance(val, dict) and "english" in val:
                    all_translations.append(val)
    except Exception as e:
        log(f"Error loading {f}: {e}")

log(f"Loaded {len(all_translations)} translation entries")

# Encode each translation
encoded = []
errors = 0
for entry in all_translations:
    if not isinstance(entry, dict): continue
    english = entry.get("english", "")
    if not english: continue
    
    try:
        glyphs = encode_text(english)
        glyph_bytes = b"".join(struct.pack(">H", g) for g in glyphs)
        
        encoded.append({
            "resource": entry.get("resource", "?"),
            "message": entry.get("message", "?"),
            "japanese": entry.get("japanese", ""),
            "english": english,
            "glyphs": glyphs,
            "byte_count": len(glyph_bytes),
        })
    except Exception as e:
        errors += 1
        log(f"Error encoding '{english[:50]}': {e}")

# Save
with open("data/encoded_translations.json", "w", encoding="utf-8") as f:
    json.dump(encoded, f, ensure_ascii=False, indent=2)

log(f"\nEncoded {len(encoded)} translations ({errors} errors)")
log(f"Saved to data/encoded_translations.json")
LOG.close()

print(f"Encoded {len(encoded)} translations, {errors} errors")
print(f"Saved to data/encoded_translations.json")

# Show a few samples
for e in encoded[:5]:
    print(f"\n  EN: {e['english'][:60]}")
    print(f"  Glyphs: {len(e['glyphs'])} values, {e['byte_count']} bytes")
