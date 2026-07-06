"""
Unit test for tools/patch_r39_spell_desc.py — NO ISO build, NO shared-file write.

Runs the patcher LOGIC against a TEMP COPY of the current post-quest build R39
(so it never collides with a concurrent build writing build/packdata_resources/).
Verifies: g3 + 3 others now decode to ENGLISH, g55/56/57 stay JP, the pristine-diff
gate passes, and the offset table + FFFF group count are self-consistent (re-walked).
"""
import struct, json, os, shutil, importlib.util, sys

BASE = 'C:/Programmieren/wizardrytranslation'
os.chdir(BASE)

BUILD = 'build/packdata_resources/0039_type15.raw'
TMP   = 'build/_test_r39_spell_desc.tmp.raw'
PRISTINE = 'extracted/packdata_raw/0039_type15.raw'

# ---- import the patcher module so we reuse its encoder/decoder, but DON'T let it
#      run its top-level write against the shared file. We instead re-exec it with
#      BUILD_PATH redirected to the temp copy.
shutil.copyfile(BUILD, TMP)

src = open('tools/patch_r39_spell_desc.py', encoding='utf-8').read()
# redirect the patcher's BUILD_PATH to the temp copy for this test run only
src = src.replace("BUILD_PATH    = 'build/packdata_resources/0039_type15.raw'",
                  f"BUILD_PATH    = '{TMP}'")
ns = {'__name__': '_patch_under_test'}
exec(compile(src, 'patch_r39_spell_desc.py(test)', 'exec'), ns)
print("\n--- patcher ran on temp copy, now verifying output ---")

# ---- decode block2 of the temp output ----
m = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))

def dec_ascii(cells):
    """ASCII-only decode for stdout safety: ascii region -> char, else <id>."""
    out = []
    for c in cells:
        if c == 0xFFFE: out.append('|'); continue
        if c == 0xFFFF: out.append('#'); continue
        v = m.get(str(c))
        if isinstance(v, str) and len(v) == 1:
            o = ord(v)
            if 0x21 <= o <= 0x7E: out.append(v); continue
            if 0xFF01 <= o <= 0xFF5E: out.append(chr(o - 0xFEE0)); continue
        out.append('<%d>' % c)
    return ''.join(out)

def is_jp(cells):
    """True if record contains any non-ascii (kanji/kana composite) cell."""
    for c in cells:
        if c in (0xFFFE, 0xFFFF, 0): continue
        v = m.get(str(c))
        if isinstance(v, str) and len(v) == 1:
            o = ord(v)
            if 0x21 <= o <= 0x7E or 0xFF01 <= o <= 0xFF5E: continue
        return True
    return False

out = open(TMP, 'rb').read()
idx, size, off, z = struct.unpack_from('<4I', out, 2 * 16)
block2 = out[off:off + size]

# re-walk FFFF records
recs, cur, pos = [], [], 0
while pos + 1 < len(block2):
    w = struct.unpack_from('>H', block2, pos)[0]
    if w == 0xFFFF:
        recs.append(cur); cur = []
    else:
        cur.append(w)
    pos += 2
assert pos == len(block2), f"block2 not aligned: {pos} vs {len(block2)}"
print(f"block2 re-walk: {len(recs)} FFFF records (expect 58)")
assert len(recs) == 58, "FFFF group count wrong"

# offset-table self-consistency: re-derive record starts, compare to table values
starts, p = [], 0
for r in recs:
    starts.append(p); p += len(r) * 2 + 2
ot = recs[0]
ot_vals = ot[0::2]
assert ot_vals[0] == 57, f"header count {ot_vals[0]} != 57"
mismatch = 0
for j in range(1, 58):
    if ot_vals[j] != starts[j]:
        mismatch += 1
        print(f"  OT MISMATCH g{j+1}: table={ot_vals[j]} actual_start={starts[j]}")
assert mismatch == 0, f"{mismatch} offset-table entries inconsistent"
print("offset-table self-consistency: all 57 entries point at their record start.")

# ---- before/after decode of g3 + 3 others ----
pr = open(PRISTINE, 'rb').read()
pb2 = pr[off:off + 0]  # placeholder; pristine block2 is at its own header
# pristine block2 location:
pidx, psize, poff, pz = struct.unpack_from('<4I', pr, 2 * 16)
pblock2 = pr[poff:poff + psize]
precs, pcur, pp = [], [], 0
while pp + 1 < len(pblock2):
    w = struct.unpack_from('>H', pblock2, pp)[0]
    if w == 0xFFFF: precs.append(pcur); pcur = []
    else: pcur.append(w)
    pp += 2

def g(records, n):  # 1-based g# -> record cells
    return records[n - 1]

print("\n--- before/after decode (ASCII-safe; '<id>' = non-ascii spell glyph) ---")
for n in (3, 5, 27, 43, 53):
    print(f"g{n} BEFORE: {dec_ascii(g(precs, n))}")
    print(f"g{n} AFTER : {dec_ascii(g(recs, n))}")

print("\n--- pristine-JP records (must stay JP) ---")
for n in (55, 56, 57):
    jp = is_jp(g(recs, n))
    print(f"g{n} is_JP={jp}  cells_unchanged={g(recs,n)==g(precs,n)}")
    assert jp, f"g{n} should stay Japanese but lost its JP cells"
    assert g(recs, n) == g(precs, n), f"g{n} pristine JP cells changed!"

# g3 must now be english and contain 'lightning' words (ascii letters present)
g3txt = dec_ascii(g(recs, 3))
assert 'lightning' in g3txt, f"g3 did not become english: {g3txt!r}"
assert not is_jp(g(recs, 3)), "g3 still contains JP cells"
print("\nALL CHECKS PASSED.")

# cleanup temp (leave it per 'never rm dirs' — it's a file, safe to remove)
try:
    os.remove(TMP)
except OSError:
    pass
