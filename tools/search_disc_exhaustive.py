#!/usr/bin/env python3
"""Exhaustive search: scan the ENTIRE disc (1.2GB) for 'seneki' and 'hisan'."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

iso_path = 'C:/Programmieren/wizardrytranslation/Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso'

# Search for 悲惨 and 戦役 in SJIS across the entire disc
targets = {
    'hisan_sjis': '\u60b2\u60e8'.encode('shift-jis'),    # 94df8e53
    'seneki_sjis': '\u6226\u5f79'.encode('shift-jis'),    # 90ed96f0
    'bankuoo_sjis': '\u30d0\u30f3\u30af'.encode('shift-jis'),  # 836f83938340
    'hisan_eucjp': '\u60b2\u60e8'.encode('euc-jp'),
    'seneki_eucjp': '\u6226\u5f79'.encode('euc-jp'),
    'hisan_u16le': '\u60b2\u60e8'.encode('utf-16-le'),
    'seneki_u16le': '\u6226\u5f79'.encode('utf-16-le'),
    'hitobito_sjis': '\u4eba\u3005'.encode('shift-jis'),  # 906c8158
}

print("Targets:")
for name, target in targets.items():
    print(f"  {name}: {target.hex()}")

print("\nScanning entire disc...")
chunk_size = 10 * 1024 * 1024
overlap = 10  # bytes overlap between chunks

with open(iso_path, 'rb') as f:
    offset = 0
    total_found = {k: 0 for k in targets}
    while True:
        if offset > 0:
            f.seek(offset - overlap)
            chunk = f.read(chunk_size + overlap)
            search_from = overlap
        else:
            chunk = f.read(chunk_size)
            search_from = 0

        if not chunk or len(chunk) <= search_from:
            break

        for name, target in targets.items():
            pos = search_from
            while True:
                pos = chunk.find(target, pos)
                if pos < 0:
                    break
                abs_pos = offset - (overlap if offset > 0 else 0) + pos
                # Get context
                ctx_start = max(0, pos - 20)
                ctx_end = min(len(chunk), pos + len(target) + 40)
                ctx = chunk[ctx_start:ctx_end]
                print(f"  {name} at disc offset 0x{abs_pos:08X} (sector {abs_pos//2048})")
                print(f"    hex: {ctx.hex()}")
                # Try SJIS decode
                try:
                    decoded = ctx.decode('shift-jis', errors='replace')
                    print(f"    sjis: {decoded[:60]}")
                except:
                    pass
                total_found[name] += 1
                pos += 1

        offset += chunk_size
        if offset % (100 * 1024 * 1024) == 0:
            print(f"  ... scanned {offset/1024/1024:.0f} MB")

print(f"\nTotal disc size scanned: {offset/1024/1024:.0f} MB")
print("Results:")
for name, count in total_found.items():
    print(f"  {name}: {count} matches")

print("\n=== Done ===")
