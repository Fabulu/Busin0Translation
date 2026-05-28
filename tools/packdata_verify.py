#!/usr/bin/env python3
"""Second-pass analysis of PACKDATA.DIG focusing on confirmed findings."""
import struct, os

INPUT = r"C:\Programmieren\wizardrytranslation\extracted\PACKDATA.DIG"
OUTFILE = r"C:\Programmieren\wizardrytranslation\dumps\packdata_toc_analysis2.txt"

def main():
    file_size = os.path.getsize(INPUT)
    lines = []
    def log(msg=""):
        print(msg)
        lines.append(msg)

    with open(INPUT, "rb") as f:
        f.seek(0)
        toc = f.read(262144)  # 256KB of TOC

        entries = []
        for i in range(0, len(toc) - 11, 12):
            a, b, c = struct.unpack_from("<III", toc, i)
            entries.append((a, b, c))

        # Find all breaks in cumulative property
        log("=== All breaks in A[i+1] == A[i] + B[i] ===")
        breaks = []
        for i in range(len(entries) - 1):
            expected = entries[i][0] + entries[i][1]
            actual = entries[i+1][0]
            if expected != actual:
                breaks.append(i)
                log(f"  Break at {i}: A[{i}]=0x{entries[i][0]:x}+B=0x{entries[i][1]:x}=0x{expected:x}, A[{i+1}]=0x{actual:x}")
                if i+2 < len(entries) and expected == entries[i+2][0]:
                    log(f"    -> Entry {i+1} is outlier; {i+2} continues from {i}")
        log(f"Total breaks: {len(breaks)}")
        log()

        # If entry 1370 is an outlier, the real entries skip it
        # Count real entries (excluding outliers)
        real_entries = []
        i = 0
        while i < len(entries):
            a, b, c = entries[i]
            if i > 0 and i in [br + 1 for br in breaks]:
                # Check if this is an outlier (next entry continues from prev)
                prev_expected = entries[i-1][0] + entries[i-1][1]
                if i+1 < len(entries) and entries[i+1][0] == prev_expected:
                    log(f"Skipping outlier entry {i}: A=0x{a:x} B=0x{b:x} C=0x{c:x}")
                    i += 1
                    continue
            real_entries.append((i, a, b, c))
            i += 1

        log(f"\nTotal entries (raw): {len(entries)}")
        log(f"Real entries (no outliers): {len(real_entries)}")

        # Find where real entries end (all-zero or A stops growing)
        last_real = 0
        for idx, (orig_i, a, b, c) in enumerate(real_entries):
            if a == 0 and b == 0 and c == 0 and idx > 10:
                log(f"First all-zero real entry at index {idx} (orig {orig_i})")
                last_real = idx
                break
            last_real = idx

        # Get the final A value (total sectors used)
        final_a = real_entries[last_real][1]  # A of last entry
        final_b = real_entries[last_real][2]  # B of last entry
        total_sectors = final_a + final_b
        log(f"Last entry A=0x{final_a:x} B=0x{final_b:x}")
        log(f"Total sectors implied: 0x{total_sectors:x} = {total_sectors}")
        log()

        # Check total_sectors * sector_size vs file_size
        for ss in [2048, 4096, 512, 1024, 256]:
            total = total_sectors * ss
            log(f"  sector_size={ss}: total=0x{total:x} ({total/1024/1024:.1f}MB) vs file=0x{file_size:x} ({file_size/1024/1024:.1f}MB)")
            if abs(total - file_size) < file_size * 0.01:
                log(f"    *** CLOSE MATCH! diff={file_size - total}")
        log()

        # Check data at A*2048 with detailed header analysis
        log("=== Data at A*2048 for first 30 entries ===")
        for idx in range(min(30, len(real_entries))):
            orig_i, a, b, c = real_entries[idx]
            off = a * 2048
            if 0 < off < file_size - 64:
                f.seek(off)
                data = f.read(64)
                v1, v2 = struct.unpack_from("<II", data, 0)
                bsize = b * 2048
                log(f"  [{orig_i:4d}] off=0x{off:08x} B*2048=0x{bsize:x} C={c}")
                log(f"         first32: {data[:32].hex()}")
                log(f"         v1=0x{v1:x} v2=0x{v2:x} (v2 fits in B*2048: {'YES' if v2 <= bsize and v2 > 0 else 'no'})")

        # Also check: maybe the data starts at A*2048 + 8 (skipping the sub-header)
        log()
        log("=== Check if bytes 8-16 at A*2048 look like known formats ===")
        for idx in range(min(30, len(real_entries))):
            orig_i, a, b, c = real_entries[idx]
            off = a * 2048
            if 0 < off < file_size - 64:
                f.seek(off + 8)
                data = f.read(16)
                # Try known magics
                for magic, name in [(b"TIM2", "TIM2"), (b"VAGp", "VAG"), (b"\x89PNG", "PNG")]:
                    if data[:len(magic)] == magic:
                        log(f"  [{orig_i}] off+8: {name}!")

        # Check what the data looks like for different C values
        log()
        log("=== Sample data by C value (type) ===")
        c_samples = {}
        for idx in range(min(500, len(real_entries))):
            orig_i, a, b, c_val = real_entries[idx]
            if c_val not in c_samples:
                c_samples[c_val] = []
            if len(c_samples[c_val]) < 3:
                off = a * 2048
                if 0 < off < file_size - 64:
                    f.seek(off)
                    data = f.read(64)
                    c_samples[c_val].append((orig_i, a, b, data))

        for c_val in sorted(c_samples.keys()):
            log(f"\n  C={c_val} (0x{c_val:x}):")
            for orig_i, a, b, data in c_samples[c_val]:
                v1, v2 = struct.unpack_from("<II", data, 0)
                log(f"    [{orig_i:4d}] A=0x{a:x} B=0x{b:x} first16={data[:16].hex()} v1=0x{v1:x} v2=0x{v2:x}")

        # CRITICAL: Check the RIFF at 0x5072d -- does it correlate with any entry?
        riff_off = 0x5072d
        riff_sector_2048 = riff_off // 2048  # = 0x283
        riff_sector_4096 = riff_off // 4096
        log(f"\n=== RIFF found at 0x{riff_off:x} ===")
        log(f"  sector (2048): 0x{riff_sector_2048:x} (remainder: 0x{riff_off % 2048:x})")
        log(f"  sector (4096): 0x{riff_sector_4096:x} (remainder: 0x{riff_off % 4096:x})")
        # Check if any entry's A matches this sector
        for idx in range(min(500, len(real_entries))):
            orig_i, a, b, c_val = real_entries[idx]
            if a <= riff_sector_2048 < a + b:
                log(f"  RIFF falls within entry [{orig_i}] A=0x{a:x} B=0x{b:x} C={c_val}")
                log(f"    entry covers sectors 0x{a:x}-0x{a+b:x}, file offset 0x{a*2048:x}-0x{(a+b)*2048:x}")
                # Read the sub-header at this entry
                entry_off = a * 2048
                f.seek(entry_off)
                data = f.read(64)
                v1, v2 = struct.unpack_from("<II", data, 0)
                log(f"    entry data: {data[:32].hex()}")
                log(f"    v1=0x{v1:x} v2=0x{v2:x}")
                # Check if RIFF offset relative to entry start
                rel = riff_off - entry_off
                log(f"    RIFF relative to entry start: 0x{rel:x} ({rel} bytes)")

        # VIF/GIF at 0x1a9000
        vif_off = 0x1a9000
        vif_sector = vif_off // 2048
        log(f"\n=== VIF/GIF data at 0x{vif_off:x} ===")
        log(f"  sector (2048): 0x{vif_sector:x}")
        for idx in range(min(500, len(real_entries))):
            orig_i, a, b, c_val = real_entries[idx]
            if a <= vif_sector < a + b:
                log(f"  Falls within entry [{orig_i}] A=0x{a:x} B=0x{b:x} C={c_val}")
                entry_off = a * 2048
                f.seek(entry_off)
                data = f.read(32)
                v1, v2 = struct.unpack_from("<II", data, 0)
                log(f"    entry data: {data[:16].hex()}")
                log(f"    v1=0x{v1:x} v2=0x{v2:x}")

        # PS2 model at 0x1e4800
        model_off = 0x1e4800
        model_sector = model_off // 2048
        log(f"\n=== PS2 model at 0x{model_off:x} ===")
        log(f"  sector (2048): 0x{model_sector:x}")
        for idx in range(min(500, len(real_entries))):
            orig_i, a, b, c_val = real_entries[idx]
            if a <= model_sector < a + b:
                log(f"  Falls within entry [{orig_i}] A=0x{a:x} B=0x{b:x} C={c_val}")
                entry_off = a * 2048
                f.seek(entry_off)
                data = f.read(32)
                v1, v2 = struct.unpack_from("<II", data, 0)
                log(f"    entry data: {data[:16].hex()}")
                log(f"    v1=0x{v1:x} v2=0x{v2:x}")

    os.makedirs(os.path.dirname(OUTFILE), exist_ok=True)
    with open(OUTFILE, "w", encoding="utf-8") as out:
        out.write("\n".join(lines))
    log(f"\nSaved to {OUTFILE}")

if __name__ == "__main__":
    main()
