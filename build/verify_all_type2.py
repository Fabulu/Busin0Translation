"""
Run the Section 1 verifier on ALL patched type-02 resources.
This checks that every DISPLAY_TEXT and SET_NAME_REF opcode
in Section 1 points to valid positions in Section 2.
"""
import sys, os
os.chdir('C:/Programmieren/wizardrytranslation')
sys.path.insert(0, 'tools')

from patch_section1_offsets import verify_patched

orig_dir = 'extracted/packdata_raw'
built_dir = 'build/packdata_resources'

total_issues = 0
total_checked = 0

for f in sorted(os.listdir(built_dir)):
    if not f.endswith('.raw') or '_type02' not in f:
        continue
    idx = int(f.split('_')[0])
    built_path = os.path.join(built_dir, f)
    orig_path = os.path.join(orig_dir, f)
    if not os.path.exists(orig_path):
        continue

    # Only check modified resources
    b = open(built_path, 'rb').read()
    o = open(orig_path, 'rb').read()
    if b == o:
        continue

    total_checked += 1
    try:
        issues, text_ops, name_ops = verify_patched(orig_path, built_path)
        if issues:
            print(f"\nR{idx:04d}: {len(issues)} ISSUES (text_ops={text_ops}, name_ops={name_ops})")
            for iss in issues:
                print(f"  {iss}")
            total_issues += len(issues)
        else:
            print(f"R{idx:04d}: OK (text_ops={text_ops}, name_ops={name_ops})")
    except Exception as ex:
        print(f"R{idx:04d}: ERROR: {ex}")
        total_issues += 1

print(f"\n{'='*60}")
print(f"Checked {total_checked} modified type-02 resources")
print(f"Total issues: {total_issues}")
