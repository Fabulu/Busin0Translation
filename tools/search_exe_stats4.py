import json, sys, glob
sys.stdout.reconfigure(encoding='utf-8')

# Find translations for R37 msg 123 and R40 msg 44
print("=== Looking for R37 msg 123 and R40 msg 44 translations ===")
for f in sorted(glob.glob('data/translate_chunks/*.json')):
    data = json.load(open(f, encoding='utf-8'))
    for entry in data:
        r = entry.get('resource')
        m = entry.get('message')
        if (r == 37 and m in range(115, 126)) or (r == 40 and m in range(40, 56)):
            print(f"  {f}: R{r} msg[{m}]: JP={entry.get('japanese','')[:60]}")
            print(f"    EN={entry.get('english','')[:60]}")

# Also check: does the build script for R38 actually work? Check for msg 2 (力/STR)
print("\n=== R38 msg 2 (力/STR) translation ===")
for f in sorted(glob.glob('data/translate_chunks/*.json')):
    data = json.load(open(f, encoding='utf-8'))
    for entry in data:
        if entry.get('resource') == 38 and entry.get('message') == 2:
            print(f"  {f}: R38 msg[2]: JP={entry.get('japanese','')[:40]} -> EN={entry.get('english','')[:40]}")

# Check if msg 2 is missing from chunk_r38_fix.json
print("\n=== All R38 messages in chunk_r38_fix.json ===")
data = json.load(open('data/translate_chunks/chunk_r38_fix.json', encoding='utf-8'))
msg_ids = sorted([e['message'] for e in data])
print(f"  Message IDs: {msg_ids[:30]}...")
print(f"  Total: {len(msg_ids)} messages")
# Check for gaps in first 20
for i in range(20):
    if i not in msg_ids:
        print(f"  MISSING: msg[{i}]")

# Check how build_full_english_v2 handles R38
print("\n=== Build script R38 handling ===")
import os
for script in ['build/build_full_english_v2.py', 'build/build_v9.py']:
    if os.path.exists(script):
        content = open(script, encoding='utf-8').read()
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'r38' in line.lower() or '0038' in line:
                print(f"  {script}:{i+1}: {line.strip()[:100]}")
