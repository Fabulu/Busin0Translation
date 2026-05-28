import re
import sys

exe_path = r"C:\Programmieren\wizardrytranslation\extracted_busin1\SLUS_202.59"
out_path = r"C:\Programmieren\wizardrytranslation\runs\CLAUDE-RUNS\RUN-20260522-1932-initial-recon\subagents\recon17-exe-compare\scan_results.txt"

with open(exe_path, "rb") as f:
    data = f.read()

out = []
def p(s=""):
    out.append(s)

p(f"File size: {len(data)} bytes")

strings = [(m.start(), m.group().decode('ascii')) for m in re.finditer(rb'[\x20-\x7e]{4,}', data)]
p(f"Total ASCII strings (>=4 chars): {len(strings)}")
p()

p("=" * 80)
p("1. FCD_ REFERENCES")
p("=" * 80)
fcd_strings = [(off, s) for off, s in strings if 'FCD_' in s or 'fcd_' in s]
for off, s in fcd_strings:
    p(f"  0x{off:08X}: {s}")
p(f"  Total: {len(fcd_strings)}")

p()
p("=" * 80)
p("2. MSG / EVE / DAT FILE REFERENCES")
p("=" * 80)
file_strings = [(off, s) for off, s in strings if any(ext in s.upper() for ext in ['.MSG', '.EVE', '.DAT', '.BIN', '.TM2', '.FCD', '.SQ2', '.DSI'])]
for off, s in file_strings:
    p(f"  0x{off:08X}: {s}")
p(f"  Total: {len(file_strings)}")

p()
p("=" * 80)
p("3. TEXTEVENT / MESSAGE SYSTEM REFERENCES")
p("=" * 80)
text_strings = [(off, s) for off, s in strings if any(kw in s for kw in ['TextEvent', 'MessageData', 'WallEvent', 'EventCommand', 'MsgLink', 'MsgIdle', 'TEXTEVENT'])]
for off, s in text_strings:
    p(f"  0x{off:08X}: {s}")
p(f"  Total: {len(text_strings)}")

p()
p("=" * 80)
p("4. FILE PATHS")
p("=" * 80)
path_strings = [(off, s) for off, s in strings if any(kw in s.lower() for kw in ['cdrom', 'host:', 'path', 'directory', 'bsn', 'dsi']) and len(s) > 4]
for off, s in path_strings:
    p(f"  0x{off:08X}: {s}")
p(f"  Total: {len(path_strings)}")

p()
p("=" * 80)
p("5. DATA LOADING / SYSTEM FUNCTIONS")
p("=" * 80)
load_strings = [(off, s) for off, s in strings if any(kw in s for kw in ['Read', 'Load', 'Kill', 'Init', 'Free', 'Close', 'Delete', 'Create']) and any(kw2 in s for kw2 in ['Battle', 'Item', 'Dungeon', 'Camp', 'Guild', 'Npc', 'Monster', 'Player', 'Effect', 'Font', 'System', 'Data', 'Field', 'Scene', 'Model', 'Texture', 'Message'])]
for off, s in load_strings:
    p(f"  0x{off:08X}: {s}")
p(f"  Total: {len(load_strings)}")

p()
p("=" * 80)
p("6. DEBUG / ERROR MESSAGES")
p("=" * 80)
debug_strings = [(off, s) for off, s in strings if any(kw in s for kw in ['Error', 'ERROR', 'error', 'Debug', 'DEBUG', 'Warning', 'WARN', 'Failed', 'FAILED', 'faild']) and len(s) > 8]
for off, s in debug_strings[:80]:
    p(f"  0x{off:08X}: {s}")
p(f"  Total: {len(debug_strings)} (showing first 80)")

p()
p("=" * 80)
p("7. GAME-SPECIFIC TERMS")
p("=" * 80)
wiz_strings = [(off, s) for off, s in strings if any(kw in s for kw in ['Wizard', 'wizard', 'Busin', 'BUSIN', 'SLUS', 'SLPS', 'Magic', 'Spell', 'spell', 'Dungeon', 'dungeon', 'Guild', 'guild', 'Party', 'party'])]
for off, s in wiz_strings:
    p(f"  0x{off:08X}: {s}")
p(f"  Total: {len(wiz_strings)}")

p()
p("=" * 80)
p("8. FORMAT STRINGS")
p("=" * 80)
fmt_strings = [(off, s) for off, s in strings if any(c in s for c in ['%s', '%d', '%x']) and len(s) > 6]
for off, s in fmt_strings[:60]:
    p(f"  0x{off:08X}: {s}")
p(f"  Total: {len(fmt_strings)} (showing first 60)")

p()
p("=" * 80)
p("9. ALL UNIQUE FCD_ RESOURCE NAMES")
p("=" * 80)
fcd_names = set()
for off, s in strings:
    for m in re.finditer(r'FCD_\w+', s):
        fcd_names.add(m.group())
for name in sorted(fcd_names):
    p(f"  {name}")
p(f"  Total unique FCD_ names: {len(fcd_names)}")

p()
p("=" * 80)
p("10. WAKU (frame/window) STRINGS")
p("=" * 80)
waku_strings = [(off, s) for off, s in strings if 'Waku' in s or 'waku' in s]
for off, s in waku_strings:
    p(f"  0x{off:08X}: {s}")
p(f"  Total: {len(waku_strings)}")

result = "\n".join(out)
with open(out_path, "w", encoding="utf-8") as f:
    f.write(result)
print(f"Results written. Lines: {len(out)}")
