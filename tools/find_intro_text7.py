#!/usr/bin/env python3
"""Search ALL resources for the CORRECT glyph pair for 十年: 1186 + 684."""
import struct, json, os, sys
sys.stdout.reconfigure(encoding='utf-8')
os.chdir("C:/Programmieren/wizardrytranslation")

manifest = json.load(open('extracted/packdata_resources/manifest.json', encoding='utf-8'))

# Correct byte pair for 十年
target = struct.pack('>HH', 1186, 684)
print(f"Searching for 0x{1186:04X} 0x{684:04X} (十年 actual glyph IDs)")

results = []
for i, entry in enumerate(manifest):
    if entry.get('skipped'):
        continue
    tc = entry['type_code']
    path = f'extracted/packdata_raw/{i:04d}_type{tc:02d}.raw'
    if not os.path.exists(path):
        continue
    data = open(path, 'rb').read()
    pos = data.find(target)
    while pos >= 0:
        results.append((i, tc, pos, len(data)))
        pos = data.find(target, pos + 1)

print(f"\nFound in {len(set(r[0] for r in results))} resources, {len(results)} total occurrences:")
for ri, tc, pos, sz in results:
    print(f"  R{ri} (type {tc}): at offset {pos} (size {sz})")
