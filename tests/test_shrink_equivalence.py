"""L0 pre-build gate: prove our compact strncpy replacement is behaviourally
identical to the ORIGINAL strncpy @0x121568 before it ships.

Two independent oracles, no trust required:
  (A) a Python C-strncpy reference, and
  (B) the ORIGINAL routine's OWN scalar tail (0x1216D0..0x121720) executed in
      tools/mips_interp.py -- same bytes the game ships, just the non-SIMD path.
Our replacement is run in the interpreter and must match BOTH across an
exhaustive matrix (every n up to 64 + large sizes, every NUL position spanning
the pad path k<n AND the no-terminator path k>=n, a few alignments), with
0xCC-poisoned dst + 0xEE guard bands to catch stray writes.

A self-proving NEGATIVE test feeds deliberately-wrong replacements and asserts
the gate goes RED -- so a green result means something.
"""
import os
import sys
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import mips_interp as MI  # noqa: E402

EXE = os.path.join(ROOT, "extracted", "SLPM_653.78")
STRNCPY_VA = 0x121568
STRNCPY_LEN = 444
SCALAR_ENTRY = 0x1216D0                     # the original's non-SIMD tail
def fo(va): return va - 0x100000 + 0x80

REG = {'zero': 0, 'at': 1, 'v0': 2, 'v1': 3, 'a0': 4, 'a1': 5, 'a2': 6, 'a3': 7,
       't0': 8, 't1': 9, 'ra': 31}


def assemble(prog):
    """Tiny label-aware assembler for the replacement. Returns bytes."""
    addr = {}
    insns = []
    pc = 0
    for item in prog:
        if isinstance(item, str):
            addr[item] = pc
        else:
            insns.append((pc, item))
            pc += 4
    out = []
    for pc, it in insns:
        m = it[0]
        if m == 'daddu':
            _, rd, rs, rt = it
            w = (REG[rs] << 21) | (REG[rt] << 16) | (REG[rd] << 11) | 0x2D
        elif m == 'addiu':
            _, rt, rs, im = it
            w = (0x09 << 26) | (REG[rs] << 21) | (REG[rt] << 16) | (im & 0xFFFF)
        elif m == 'lbu':
            _, rt, off, rs = it
            w = (0x24 << 26) | (REG[rs] << 21) | (REG[rt] << 16) | (off & 0xFFFF)
        elif m == 'sb':
            _, rt, off, rs = it
            w = (0x28 << 26) | (REG[rs] << 21) | (REG[rt] << 16) | (off & 0xFFFF)
        elif m in ('beq', 'bne'):
            _, rs, rt, lab = it
            opc = 0x04 if m == 'beq' else 0x05
            off = (addr[lab] - (pc + 4)) // 4
            w = (opc << 26) | (REG[rs] << 21) | (REG[rt] << 16) | (off & 0xFFFF)
        elif m == 'jr':
            _, rs = it
            w = (REG[rs] << 21) | 0x08
        elif m == 'nop':
            w = 0
        else:
            raise ValueError("asm: %r" % (it,))
        out.append(w)
    return b"".join(struct.pack("<I", w) for w in out)


# ---- our compact strncpy replacement (a0=dst, a1=src, a2=n -> v0=dst) ----
REPLACEMENT = [
    ('daddu', 't0', 'a0', 'zero'),          # t0 = dst (saved for return)
    'COPY',
    ('beq', 'a2', 'zero', 'DONE'),          # n == 0 -> done
    ('nop',),
    ('lbu', 'v0', 0, 'a1'),                 # v0 = *src
    ('addiu', 'a1', 'a1', 1),               # src++
    ('sb', 'v0', 0, 'a0'),                  # *dst = v0  (writes the NUL too)
    ('addiu', 'a0', 'a0', 1),               # dst++
    ('addiu', 'a2', 'a2', -1),              # n--
    ('bne', 'v0', 'zero', 'COPY'),          # v0 != 0 -> keep copying
    ('nop',),
    'PAD',                                  # v0 was 0: zero-fill remaining n
    ('beq', 'a2', 'zero', 'DONE'),
    ('nop',),
    ('sb', 'zero', 0, 'a0'),
    ('addiu', 'a0', 'a0', 1),
    ('addiu', 'a2', 'a2', -1),
    ('beq', 'zero', 'zero', 'PAD'),
    ('nop',),
    'DONE',
    ('jr', 'ra'),
    ('daddu', 'v0', 't0', 'zero'),          # v0 = dst  (delay slot)
]

# a deliberately-broken variant that copies PAST the NUL and never pads
BROKEN = [
    ('daddu', 't0', 'a0', 'zero'),
    'L',
    ('beq', 'a2', 'zero', 'D'),
    ('nop',),
    ('lbu', 'v0', 0, 'a1'),
    ('addiu', 'a1', 'a1', 1),
    ('sb', 'v0', 0, 'a0'),
    ('addiu', 'a0', 'a0', 1),
    ('addiu', 'a2', 'a2', -1),
    ('beq', 'zero', 'zero', 'L'),           # BUG: always loops, ignores NUL, no pad
    ('nop',),
    'D',
    ('jr', 'ra'),
    ('daddu', 'v0', 't0', 'zero'),
]


def c_strncpy(src, n):
    """Reference C strncpy. `src` must have >= n readable bytes. Returns n bytes."""
    res = bytearray(n)
    stop = False
    for i in range(n):
        if not stop and src[i] != 0:
            res[i] = src[i]
        else:
            stop = True   # res[i] stays 0
    return bytes(res)


DST_BASE = 0x00300000
SRC_BASE = 0x00200000
CODE_BASE = 0x00400000
GUARD = 8


def _make_mem(src_bytes, n, dst_align, src_align, code):
    mem = MI.Mem()
    # dst region: [GUARD 0xEE][n bytes 0xCC][GUARD 0xEE]
    dbase = DST_BASE + dst_align
    dst_region = bytearray(b"\xEE" * GUARD + b"\xCC" * n + b"\xEE" * GUARD)
    mem.add(dbase - GUARD, dst_region)
    # src region: content padded to at least n+GUARD readable bytes
    sbase = SRC_BASE + src_align
    mem.add(sbase, src_bytes)
    mem.add(CODE_BASE, code)
    return mem, dbase, sbase


def _read_dst(mem, dbase, n):
    return bytes(mem.load(dbase + i, 1, False) for i in range(n))


def _guards_intact(mem, dbase, n):
    lo = all(mem.load(dbase - GUARD + i, 1, False) == 0xEE for i in range(GUARD))
    hi = all(mem.load(dbase + n + i, 1, False) == 0xEE for i in range(GUARD))
    return lo and hi


def _run_code(code, code_base, entry, mem, dbase, sbase, n, extra=None):
    regs = {'a0': dbase, 'a1': sbase, 'a2': n, 'ra': 0x0BADF00D}
    if extra:
        regs.update(extra)
    v0 = MI.run(code_base, code, mem, regs, entry)
    return v0 & 0xFFFFFFFF


def _cases():
    ns = list(range(0, 65)) + [65, 96, 127, 128, 129, 200, 255, 256]
    for n in ns:
        # NUL positions: pad path (k<n) and no-terminator path (k>=n)
        ks = sorted(set([0, 1, 2, max(0, n - 1)] + [n, n + 1, n + 3]))
        for k in ks:
            for dal, sal in ((0, 0), (1, 3), (7, 5), (3, 12)):
                yield n, k, dal, sal


def _build_src(n, k):
    # readable length must cover the no-terminator path (n bytes) + slack
    size = n + GUARD + 4
    buf = bytearray(((1 + (i % 253)) & 0xFF) for i in range(size))  # all non-zero
    if k < size:
        buf[k] = 0
    return bytes(buf)


def main():
    if not os.path.exists(EXE):
        print("SKIP test_shrink_equivalence: %s not present" % EXE)
        return 0
    exe = open(EXE, "rb").read()
    orig = exe[fo(STRNCPY_VA):fo(STRNCPY_VA) + STRNCPY_LEN]
    # SINGLE SOURCE: prove the bytes patch_exe actually ships, not a parallel copy.
    sys.path.insert(0, os.path.join(ROOT, "build"))
    import _reloc_v147_design as RELOC  # noqa: E402
    repl = RELOC.build_strncpy_replacement()
    assert repl == assemble(REPLACEMENT), (
        "shipped build_strncpy_replacement() has DRIFTED from this test's design words")
    broken = assemble(BROKEN)
    print("replacement strncpy: %d bytes (%d instrs); original: %d bytes -> frees %d"
          % (len(repl), len(repl) // 4, STRNCPY_LEN, STRNCPY_LEN - len(repl)))
    assert len(repl) <= STRNCPY_LEN, "replacement bigger than original!"

    fails = 0
    checked = 0
    for n, k, dal, sal in _cases():
        src = _build_src(n, k)
        oracle = c_strncpy(src[:n] if n <= len(src) else src, n)

        # (B) original scalar tail as an independent oracle
        memB, dbB, sbB = _make_mem(src, n, dal, sal, orig)
        vB = _run_code(orig, STRNCPY_VA, SCALAR_ENTRY, memB, dbB, sbB, n,
                       extra={'t0': dbB})
        dstB = _read_dst(memB, dbB, n)
        if dstB != oracle:
            fails += 1
            if fails <= 3:
                print("  [!!] ORIG-tail != C-oracle  n=%d k=%d: %r vs %r" % (n, k, dstB, oracle))

        # our replacement vs the oracle
        memR, dbR, sbR = _make_mem(src, n, dal, sal, repl)
        vR = _run_code(repl, CODE_BASE, CODE_BASE, memR, dbR, sbR, n)
        dstR = _read_dst(memR, dbR, n)
        ok = (dstR == oracle == dstB and vR == dbR and vB == dbB
              and _guards_intact(memR, dbR, n))
        if not ok:
            fails += 1
            if fails <= 6:
                print("  [!!] REPL mismatch n=%d k=%d dal=%d sal=%d: dst=%r want=%r v0=0x%X(want 0x%X) guards=%s"
                      % (n, k, dal, sal, dstR, oracle, vR, dbR, _guards_intact(memR, dbR, n)))
        checked += 1

    # ---- self-proving NEGATIVE test: the broken variant MUST mismatch ----
    neg_caught = False
    for n, k, dal, sal in [(16, 4, 0, 0), (8, 2, 0, 0), (32, 10, 0, 0)]:
        src = _build_src(n, k)
        oracle = c_strncpy(src[:n], n)
        mem, db, sb = _make_mem(src, n, dal, sal, broken)
        try:
            _run_code(broken, CODE_BASE, CODE_BASE, mem, db, sb, n)
            if _read_dst(mem, db, n) != oracle or not _guards_intact(mem, db, n):
                neg_caught = True
        except MI.Trap:
            neg_caught = True
    if not neg_caught:
        print("  [!!] NEGATIVE test failed: harness did NOT catch a broken strncpy")
        fails += 1

    print("checked %d cases (dual-oracle); negative-test caught broken=%s" % (checked, neg_caught))
    if fails:
        print("test_shrink_equivalence: %d FAILURES" % fails)
        return 1
    print("test_shrink_equivalence: PASS (replacement == original strncpy across all cases)")
    return 0


def test_strncpy_shrink_equivalence():
    """Suite entry: the shrunk strncpy must be byte-for-byte equivalent to the original."""
    assert main() == 0, "strncpy shrink replacement is NOT equivalent to the original"


TESTS = [test_strncpy_shrink_equivalence]

if __name__ == "__main__":
    sys.exit(main())
