"""
Scan PS2 EE RAM dump for PACKDATA resources loaded during chargen.
Searches for the first N bytes of each resource in the 32MB RAM.
"""
import os, sys, struct, time

RAM_PATH = r"C:\Programmieren\wizardrytranslation\RAMdumps\27-5_extracted\eeMemory.bin"
RAW_DIR  = r"C:\Programmieren\wizardrytranslation\extracted\packdata_raw"
PATCHED_DIR = r"C:\Programmieren\wizardrytranslation\build\patched_type2"

SIGNATURE_LEN = 32  # bytes to match
MIN_RESOURCE_SIZE = 64  # skip tiny resources

def main():
    print("Loading RAM dump...")
    with open(RAM_PATH, "rb") as f:
        ram = f.read()
    print(f"RAM size: {len(ram)} bytes ({len(ram)/(1024*1024):.1f} MB)")

    # List all resources
    raw_files = sorted(os.listdir(RAW_DIR))

    # Build list of patched resource indices
    patched_indices = set()
    if os.path.isdir(PATCHED_DIR):
        for fn in os.listdir(PATCHED_DIR):
            idx = int(fn.split("_")[0])
            patched_indices.add(idx)
    print(f"Patched resources: {len(patched_indices)}")

    found = []
    skipped = 0
    searched = 0
    t0 = time.time()

    for fn in raw_files:
        idx = int(fn.split("_")[0])
        rtype = fn.split("_")[1].replace(".raw","")
        fpath = os.path.join(RAW_DIR, fn)
        fsize = os.path.getsize(fpath)

        if fsize < MIN_RESOURCE_SIZE:
            skipped += 1
            continue

        with open(fpath, "rb") as f:
            sig = f.read(SIGNATURE_LEN)

        if len(sig) < SIGNATURE_LEN:
            skipped += 1
            continue

        # Skip signatures that are all zeros (common, would match everywhere)
        if sig == b'\x00' * SIGNATURE_LEN:
            skipped += 1
            continue

        searched += 1

        # Search RAM for this signature
        offset = 0
        matches = []
        while True:
            pos = ram.find(sig, offset)
            if pos == -1:
                break
            matches.append(pos)
            offset = pos + 1
            if len(matches) > 10:  # cap to avoid flood
                break

        if matches:
            is_patched = idx in patched_indices
            found.append((idx, rtype, fsize, matches, is_patched))

        if searched % 500 == 0:
            elapsed = time.time() - t0
            print(f"  Searched {searched} resources, found {len(found)} so far ({elapsed:.1f}s)")

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s. Searched {searched}, skipped {skipped}, found {len(found)} in RAM.")

    # Now for found resources, check if RAM copy matches original or patched
    print("\n=== RESOURCES FOUND IN RAM ===")
    print(f"{'Idx':>5} {'Type':>8} {'Size':>8} {'#Hits':>5} {'Patched?':>9} {'RAM Addrs'}")
    print("-" * 80)

    results = []
    for idx, rtype, fsize, matches, is_patched in sorted(found):
        addrs = ", ".join(f"0x{m:08X}" for m in matches[:5])
        if len(matches) > 5:
            addrs += f" (+{len(matches)-5} more)"
        print(f"{idx:>5} {rtype:>8} {fsize:>8} {len(matches):>5} {'YES' if is_patched else 'no':>9} {addrs}")

        # For patched resources, compare RAM copy with original and patched
        ram_match_info = ""
        if is_patched and matches:
            patched_fn = f"{idx:04d}_type02.raw"
            patched_path = os.path.join(PATCHED_DIR, patched_fn)
            orig_path = os.path.join(RAW_DIR, f"{idx:04d}_{rtype}.raw")

            if os.path.exists(patched_path) and os.path.exists(orig_path):
                with open(patched_path, "rb") as f:
                    patched_data = f.read()
                with open(orig_path, "rb") as f:
                    orig_data = f.read()

                ram_addr = matches[0]
                # Compare first min(size, fsize) bytes
                check_len = min(len(patched_data), len(orig_data), fsize, len(ram) - ram_addr)
                ram_slice = ram[ram_addr:ram_addr+check_len]

                orig_match = (ram_slice == orig_data[:check_len])
                patched_match = (ram_slice == patched_data[:check_len])

                if orig_match and not patched_match:
                    ram_match_info = "RAM=ORIGINAL"
                elif patched_match and not orig_match:
                    ram_match_info = "RAM=PATCHED"
                elif orig_match and patched_match:
                    ram_match_info = "RAM=BOTH(identical)"
                else:
                    ram_match_info = "RAM=NEITHER"

                print(f"      -> {ram_match_info}")

        results.append({
            'idx': idx, 'type': rtype, 'size': fsize,
            'matches': matches, 'is_patched': is_patched,
            'ram_match': ram_match_info
        })

    # Priority analysis
    print("\n=== PRIORITY RANGES ===")
    print("\nR1185-R1195 (chargen area):")
    for r in results:
        if 1185 <= r['idx'] <= 1195:
            addrs = ", ".join(f"0x{m:08X}" for m in r['matches'][:3])
            print(f"  R{r['idx']} ({r['type']}, {r['size']}B) @ {addrs} {r['ram_match']}")

    chargen_found = [r['idx'] for r in results if 1185 <= r['idx'] <= 1195]
    chargen_missing = [i for i in range(1185, 1196) if i not in chargen_found]
    if chargen_missing:
        print(f"  NOT found in RAM: {chargen_missing}")

    print("\nR1269-R1276 (kanji font pages):")
    for r in results:
        if 1269 <= r['idx'] <= 1276:
            addrs = ", ".join(f"0x{m:08X}" for m in r['matches'][:3])
            print(f"  R{r['idx']} ({r['type']}, {r['size']}B) @ {addrs} {r['ram_match']}")

    kanji_found = [r['idx'] for r in results if 1269 <= r['idx'] <= 1276]
    kanji_missing = [i for i in range(1269, 1277) if i not in kanji_found]
    if kanji_missing:
        print(f"  NOT found in RAM: {kanji_missing}")

    # Summary stats
    print(f"\n=== SUMMARY ===")
    print(f"Total resources found in RAM: {len(found)}")
    types = {}
    for r in results:
        types[r['type']] = types.get(r['type'], 0) + 1
    for t, c in sorted(types.items()):
        print(f"  {t}: {c}")

    patched_in_ram = [r for r in results if r['is_patched']]
    print(f"\nPatched resources found in RAM: {len(patched_in_ram)}")
    for r in patched_in_ram:
        print(f"  R{r['idx']} -> {r['ram_match']}")

    # Write results to file for report generation
    import json
    out_path = r"C:\Programmieren\wizardrytranslation\runs\CLAUDE-RUNS\RUN-20260528-remaining-japanese\chargen_ram_results.json"
    json_results = []
    for r in results:
        json_results.append({
            'idx': r['idx'], 'type': r['type'], 'size': r['size'],
            'ram_addresses': [f"0x{m:08X}" for m in r['matches']],
            'is_patched': r['is_patched'], 'ram_match': r['ram_match']
        })
    with open(out_path, 'w') as f:
        json.dump(json_results, f, indent=2)
    print(f"\nJSON results saved to: {out_path}")

if __name__ == "__main__":
    main()
