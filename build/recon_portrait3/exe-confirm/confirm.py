import sys
sys.stdout.reconfigure(encoding='utf-8')

EE = r"C:/programmieren/wizardrytranslation/build/recon_portrait3/extract/MissingPortraitAndFuckedDialogue__ee.bin"
PATCHED = r"C:/programmieren/wizardrytranslation/build/SLPM_653.78_patched"
ORIG = r"C:/programmieren/wizardrytranslation/extracted/SLPM_653.78"

# EE RAM: EXE loaded at vaddr 0x100000 = fileoff 0x100000 in eeMemory.bin
# EXE on-disk file: vaddr-0x100000+0x80 (0x80 = ELF/exe header offset on disk)
# So RAM byte at vaddr V == disk file byte at (V-0x100000)+0x80

with open(EE,'rb') as f:
    ee = f.read()
with open(PATCHED,'rb') as f:
    patched = f.read()
with open(ORIG,'rb') as f:
    orig = f.read()

print("EE size", len(ee), "patched size", len(patched), "orig size", len(orig))

# The EXE on disk has 0x80 header; the loaded segment in RAM starts at 0x100000.
# Compare disk[0x80:] to RAM[0x100000: 0x100000+len-0x80]
disk_body_patched = patched[0x80:]
disk_body_orig = orig[0x80:]
ram_body = ee[0x100000:0x100000+len(disk_body_patched)]

def cmp(name, a, b):
    diffs = sum(1 for x,y in zip(a,b) if x!=y)
    print(f"  {name}: {diffs} differing bytes out of {len(a)}")
    return diffs

print("RAM-body vs patched-disk-body:")
d_patched = cmp("vs PATCHED", ram_body, disk_body_patched)
print("RAM-body vs orig-disk-body:")
d_orig = cmp("vs ORIG", ram_body, disk_body_orig)

# Also compare patched vs orig to know how many patch bytes exist total
print("PATCHED vs ORIG disk-body diff:")
dpo = cmp("patched-vs-orig", disk_body_patched, disk_body_orig)

# Where do patched and orig differ? Those are the patch sites. Check each against RAM.
print("\n--- Patch-site verification (patched != orig sites) ---")
sites = []
i = 0
n = min(len(disk_body_patched), len(disk_body_orig))
while i < n:
    if disk_body_patched[i] != disk_body_orig[i]:
        start = i
        while i < n and disk_body_patched[i] != disk_body_orig[i]:
            i += 1
        sites.append((start, i))
    else:
        i += 1
print(f"Number of contiguous patch regions: {len(sites)}")
present = 0
absent = 0
for (s,e) in sites:
    # vaddr of this site
    vaddr = 0x100000 + s  # since disk_body index s maps to RAM 0x100000+s
    ram_slice = ram_body[s:e]
    patched_slice = disk_body_patched[s:e]
    orig_slice = disk_body_orig[s:e]
    if ram_slice == patched_slice:
        present += 1
        tag = "PATCHED"
    elif ram_slice == orig_slice:
        absent += 1
        tag = "ORIG(!)"
    else:
        tag = "OTHER"
    # print first 20 sites detail
    if len(sites) <= 60 or (s,e) in sites[:40]:
        print(f"  va=0x{vaddr:08X} len={e-s} {tag}  patched={patched_slice[:12].hex()} ram={ram_slice[:12].hex()}")
print(f"\nSites matching PATCHED: {present}, matching ORIG: {absent}, OTHER: {len(sites)-present-absent}")
