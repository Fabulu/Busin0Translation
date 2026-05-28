"""Patch save slot display names in SLPM_653.78 from Japanese to English ASCII."""
import shutil
import os
import sys

src = r"C:\Programmieren\wizardrytranslation\extracted\SLPM_653.78"
dst = r"C:\Programmieren\wizardrytranslation\build\patched_type2\SLPM_653.78"

# Copy original to build dir
shutil.copy2(src, dst)

data = bytearray(open(dst, "rb").read())

# Each tuple: (offset, available_bytes, new_ascii_string)
patches = [
    (0x3FC720, 16, "BUSIN 0"),
    (0x3FC750, 32, "BUSIN 0 Data 1"),
    (0x3FC770, 32, "BUSIN 0 Data 2"),
    (0x3FC790, 32, "BUSIN 0 Data 3"),
    (0x3F9370, 24, "BUSIN 0 Suspend"),
]

for offset, avail, text in patches:
    encoded = text.encode("ascii")
    assert len(encoded) + 1 <= avail, f"String too long: {text!r} ({len(encoded)+1} > {avail})"
    # Zero-fill the available space, then write new string + null
    for i in range(avail):
        data[offset + i] = 0
    for i, b in enumerate(encoded):
        data[offset + i] = b
    print(f"Patched 0x{offset:06X}: {text!r} ({len(encoded)} bytes + null)")

open(dst, "wb").write(data)
print(f"Written to {dst} ({len(data)} bytes)")
