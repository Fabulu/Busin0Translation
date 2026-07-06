#!/usr/bin/env python3
"""
mips_cave_analyzer.py -- a STRUCTURED MIPS (EE / R5900 subset) decoder + static
safety analyser for the EXE "caves" this project injects into SLPM-65378.

WHY THIS EXISTS
---------------
Two real regressions shipped because the ONLY cave tests were byte-equality
(they confirm the WRONG bytes were installed *correctly*):

  BUG#1  sign-extension: a table meant to sit at VA 0x4AF338 was read via
         `lui at,0x4A` + `lbu v1,0xF338(at)`.  0xF338 >= 0x8000, so the load
         offset SIGN-EXTENDS to -0xCC8 and the EFFECTIVE address is
         0x4A0000 - 0xCC8 = 0x49F338 (garbage) -> garbled chargen.  Every
         existing test compared IMMEDIATES (lui==VA>>16) and is structurally
         blind to sign-extension.

  BUG#2  register clobber: a cave used k1 (reg 27).  k0/k1 are KERNEL-live --
         the EE interrupt handler uses them as its own scratch and does NOT
         preserve them across a VBlank/DMA interrupt -> post-chargen black
         screen.  The hazard is documented in prose at build/patch_exe.py
         (~line 1040) but NOTHING enforced it.

This module is the enforcement.  It is SEEDED from the print-only decoder
build/_reloc_v147_design._disasm(), refactored to return structured Insn
objects, and adds three static checks used by tests/test_cave_semantics.py:

  * resolve_absolute_accesses  -- a linear symbolic register tracker that
                                  computes the SIGN-EXTENDED effective address
                                  of every lui-const-based load/store.
  * check_effective_addresses  -- assert every absolute access lands in an
                                  explicit ADDRESS BOOK (catches BUG#1).
  * check_no_kernel_regs       -- RULE K: ban k0/k1 in any cave word; warn on
                                  t9/gp (catches BUG#2).

capstone 5.0.7 is installed and MAY be used to cross-validate (see
capstone_crosscheck), but the GATE never depends on capstone decoding R5900
ops -- the structured decoder below is self-contained.

Coordinates: eeMemory[VA] == VA.  EXE file offset = VA - 0x100000 + 0x80.
The mode sentinel (0x4FED18) is read via `lui 0x50; lw -0x12E8(rX)`
(0x500000 + sext16(0xED18) = 0x4FED18) -- a canonical sign-extended access
that must land in the address book.
"""

MODE_SENTINEL_VA = 0x4FED18   # game render-mode word (5 chargen / 7 request / 8 battle)


# ---------------------------------------------------------------------------
# Register names (index == MIPS GPR number)
# ---------------------------------------------------------------------------
REG_NAMES = [
    'zero', 'at', 'v0', 'v1', 'a0', 'a1', 'a2', 'a3',
    't0', 't1', 't2', 't3', 't4', 't5', 't6', 't7',
    's0', 's1', 's2', 's3', 's4', 's5', 's6', 's7',
    't8', 't9', 'k0', 'k1', 'gp', 'sp', 's8', 'ra',
]

K0, K1 = 26, 27          # KERNEL-live scratch  -> RULE K hard failure
T9, GP = 25, 28          # PIC entry / global ptr -> RULE K warning


def rname(n):
    return REG_NAMES[n] if 0 <= n < 32 else "r%d" % n


# ---------------------------------------------------------------------------
# Opcode tables (the closed set the caves use, plus neighbours for safety).
# ---------------------------------------------------------------------------
# op6 -> (mnemonic, kind) for non-SPECIAL primary opcodes.
#   kinds: 'lui','load','store','iarith','branch','branch1','jump','jal'
_LOADS = {
    0x20: ('lb', 1), 0x21: ('lh', 2), 0x22: ('lwl', 4), 0x23: ('lw', 4),
    0x24: ('lbu', 1), 0x25: ('lhu', 2), 0x26: ('lwr', 4), 0x27: ('lwu', 4),
    0x37: ('ld', 8),
}
_STORES = {
    0x28: ('sb', 1), 0x29: ('sh', 2), 0x2A: ('swl', 4), 0x2B: ('sw', 4),
    0x2E: ('swr', 4), 0x3F: ('sd', 8),
}
_IARITH = {
    0x08: 'addi', 0x09: 'addiu', 0x0A: 'slti', 0x0B: 'sltiu',
    0x0C: 'andi', 0x0D: 'ori', 0x0E: 'xori',
}
# SPECIAL (op==0) funct -> (mnemonic, kind)
#   kinds: 'shift'(rd,rt[,sa]), 'shiftv'(rd,rt,rs), 'rarith'(rd,rs,rt),
#          'mov'(rd,rs,rt cond), 'jr'(rs), 'jalr'(rd,rs)
_SPECIAL = {
    0x00: ('sll', 'shift'),  0x02: ('srl', 'shift'),  0x03: ('sra', 'shift'),
    0x04: ('sllv', 'shiftv'), 0x06: ('srlv', 'shiftv'), 0x07: ('srav', 'shiftv'),
    0x38: ('dsll', 'shift'), 0x3A: ('dsrl', 'shift'), 0x3B: ('dsra', 'shift'),
    0x3C: ('dsll32', 'shift'), 0x3E: ('dsrl32', 'shift'), 0x3F: ('dsra32', 'shift'),
    0x08: ('jr', 'jr'), 0x09: ('jalr', 'jalr'),
    0x0A: ('movz', 'mov'), 0x0B: ('movn', 'mov'),
    0x20: ('add', 'rarith'), 0x21: ('addu', 'rarith'),
    0x22: ('sub', 'rarith'), 0x23: ('subu', 'rarith'),
    0x24: ('and', 'rarith'), 0x25: ('or', 'rarith'),
    0x26: ('xor', 'rarith'), 0x27: ('nor', 'rarith'),
    0x2A: ('slt', 'rarith'), 0x2B: ('sltu', 'rarith'),
    0x2C: ('dadd', 'rarith'), 0x2D: ('daddu', 'rarith'),
}


# ---------------------------------------------------------------------------
# Insn
# ---------------------------------------------------------------------------
class Insn(object):
    """One decoded MIPS instruction.

    Fields (as the spec requires): op, rs, rt, rd, sa, imm, va, mnemonic.
    Extras: word (raw u32), funct, simm (sign-extended imm), kind (semantic
    class), target (absolute j/jal target VA or None)."""

    __slots__ = ('word', 'va', 'op', 'rs', 'rt', 'rd', 'sa', 'funct',
                 'imm', 'simm', 'kind', 'mnemonic', 'target')

    def __init__(self, word, va):
        self.word = word & 0xFFFFFFFF
        self.va = va
        w = self.word
        self.op = w >> 26
        self.rs = (w >> 21) & 31
        self.rt = (w >> 16) & 31
        self.rd = (w >> 11) & 31
        self.sa = (w >> 6) & 31
        self.funct = w & 0x3F
        self.imm = w & 0xFFFF
        self.simm = self.imm - 0x10000 if self.imm >= 0x8000 else self.imm
        self.target = None
        self.kind = 'other'
        self.mnemonic = '?'
        self._classify()

    # -- classification -----------------------------------------------------
    def _classify(self):
        w, op = self.word, self.op
        if w == 0:
            self.kind, self.mnemonic = 'nop', 'nop'
            return
        if op == 0x00:                       # SPECIAL
            info = _SPECIAL.get(self.funct)
            if info:
                mn, kind = info
                self.kind = kind
                self.mnemonic = mn
            else:
                self.kind, self.mnemonic = 'special?', 'op0_%02x' % self.funct
            return
        if op == 0x01:                       # REGIMM (bltz/bgez/...)
            self.kind, self.mnemonic = 'branch1', 'regimm'
            return
        if op == 0x02:
            self.kind, self.mnemonic, self.target = 'jump', 'j', (w & 0x3FFFFFF) << 2
            return
        if op == 0x03:
            self.kind, self.mnemonic, self.target = 'jal', 'jal', (w & 0x3FFFFFF) << 2
            return
        if op in (0x04, 0x05):
            self.kind = 'branch'
            self.mnemonic = 'beq' if op == 0x04 else 'bne'
            self.target = self.va + 4 + self.simm * 4
            return
        if op in (0x06, 0x07):               # blez/bgtz (rt==0)
            self.kind = 'branch1'
            self.mnemonic = 'blez' if op == 0x06 else 'bgtz'
            self.target = self.va + 4 + self.simm * 4
            return
        if op == 0x0F:
            self.kind, self.mnemonic = 'lui', 'lui'
            return
        if op in _IARITH:
            self.kind, self.mnemonic = 'iarith', _IARITH[op]
            return
        if op in _LOADS:
            self.kind, self.mnemonic = 'load', _LOADS[op][0]
            return
        if op in _STORES:
            self.kind, self.mnemonic = 'store', _STORES[op][0]
            return
        self.kind, self.mnemonic = 'other', 'op0x%02X' % op

    # -- helpers ------------------------------------------------------------
    def size(self):
        """Access width in bytes for a load/store, else None."""
        if self.op in _LOADS:
            return _LOADS[self.op][1]
        if self.op in _STORES:
            return _STORES[self.op][1]
        return None

    def dest_reg(self):
        """The GPR this instruction writes, or None."""
        k = self.kind
        if k in ('lui', 'iarith', 'load'):
            return self.rt
        if k in ('rarith', 'shift', 'shiftv', 'mov'):
            return self.rd
        if k == 'jalr':
            return self.rd
        if k == 'jal':
            return 31            # ra
        return None

    def used_regs(self):
        """Set of GPR numbers this instruction ACTUALLY references.

        Field-aware: for I-type ops the rd/sa bit positions belong to the
        immediate, so a blind rs/rt/rd read would fabricate phantom registers
        (and phantom kernel-reg hits).  For opcodes outside the known set we
        fall back to {rs,rt,rd} conservatively so an unrecognised instruction
        can never hide a k0/k1 use."""
        k = self.kind
        if k == 'nop':
            return set()
        if k == 'lui':
            return {self.rt}
        if k in ('load', 'store', 'iarith', 'branch'):
            return {self.rs, self.rt}
        if k == 'branch1':
            return {self.rs}
        if k in ('rarith', 'shiftv', 'mov'):
            return {self.rs, self.rt, self.rd}
        if k == 'shift':
            return {self.rt, self.rd}
        if k == 'jr':
            return {self.rs}
        if k == 'jalr':
            return {self.rs, self.rd}
        if k in ('jump', 'jal'):
            return set()
        # unknown / special? -> conservative
        return {self.rs, self.rt, self.rd}

    def __repr__(self):
        return "<Insn 0x%06X %08X %s>" % (self.va, self.word, self.text())

    def text(self):
        k, mn = self.kind, self.mnemonic
        if k == 'nop':
            return 'nop'
        if k == 'lui':
            return "lui   %s,0x%X" % (rname(self.rt), self.imm)
        if k == 'load' or k == 'store':
            return "%-5s %s,%d(%s)" % (mn, rname(self.rt), self.simm, rname(self.rs))
        if k == 'iarith':
            if mn in ('andi', 'ori', 'xori'):
                return "%-5s %s,%s,0x%X" % (mn, rname(self.rt), rname(self.rs), self.imm)
            return "%-5s %s,%s,%d" % (mn, rname(self.rt), rname(self.rs), self.simm)
        if k == 'rarith' or k == 'mov':
            return "%-5s %s,%s,%s" % (mn, rname(self.rd), rname(self.rs), rname(self.rt))
        if k == 'shift':
            return "%-5s %s,%s,%d" % (mn, rname(self.rd), rname(self.rt), self.sa)
        if k == 'shiftv':
            return "%-5s %s,%s,%s" % (mn, rname(self.rd), rname(self.rt), rname(self.rs))
        if k == 'jr':
            return "jr    %s" % rname(self.rs)
        if k == 'jalr':
            return "jalr  %s,%s" % (rname(self.rd), rname(self.rs))
        if k in ('jump', 'jal'):
            return "%-5s 0x%06X" % (mn, self.target)
        if k in ('branch', 'branch1'):
            if mn in ('beq', 'bne'):
                return "%-5s %s,%s,0x%06X" % (mn, rname(self.rs), rname(self.rt), self.target)
            return "%-5s %s,0x%06X" % (mn, rname(self.rs), self.target)
        return "%s (%08X)" % (mn, self.word)


# ---------------------------------------------------------------------------
# Decode
# ---------------------------------------------------------------------------
def decode(words, base_va):
    """Decode an iterable of u32 cave words into [Insn] at consecutive VAs."""
    return [Insn(w, base_va + i * 4) for i, w in enumerate(words)]


# ---------------------------------------------------------------------------
# Symbolic register tracking -> absolute effective addresses
# ---------------------------------------------------------------------------
# state[reg] is one of:
#   ('const', v)  -- a fully-known 32-bit value (from lui / lui+ori / const arith)
#   ('base',  v)  -- a lui-const anchored base with an UNKNOWN index added
#                    (e.g. lui at,0x4B ; addu at,at,gid).  The table's BASE VA
#                    is v; the runtime index selects the element.  Verifying
#                    v + sext16(off) is exactly the table-base check BUG#1 needs.
#   absent        -- unknown
def _anchor(val):
    """Return the const anchor of a state value that can anchor a load/store."""
    if val is None:
        return None
    return val[1]


def resolve_absolute_accesses(insns):
    """Linear symbolic tracker.  Returns a list of absolute-access records:
        {va, kind:'load'/'store', mnemonic, size, ea, base_reg, imm, base_kind}
    ONLY lui-const-derived accesses are recorded; sp/gp/s-reg based loads
    self-exclude (their base never becomes a tracked const)."""
    state = {0: ('const', 0)}          # $zero is always 0
    out = []

    def setreg(r, v):
        if r == 0:
            return                     # writes to $zero are discarded
        if v is None:
            state.pop(r, None)
        else:
            state[r] = v

    for ins in insns:
        k = ins.kind

        # --- record memory accesses BEFORE mutating dest -------------------
        if k in ('load', 'store'):
            bv = state.get(ins.rs)
            anchor = _anchor(bv)
            if anchor is not None:
                ea = (anchor + ins.simm) & 0xFFFFFFFF
                out.append({
                    'va': ins.va,
                    'kind': k,
                    'mnemonic': ins.mnemonic,
                    'size': ins.size(),
                    'ea': ea,
                    'base_reg': ins.rs,
                    'imm': ins.imm,
                    'base_kind': bv[0],
                })

        # --- update register state ----------------------------------------
        if k == 'lui':
            setreg(ins.rt, ('const', (ins.imm & 0xFFFF) << 16))
        elif k == 'iarith':
            src = state.get(ins.rs)
            if ins.mnemonic == 'ori' and src is not None and src[0] == 'const':
                setreg(ins.rt, ('const', (src[1] | ins.imm) & 0xFFFFFFFF))
            elif ins.mnemonic in ('addiu', 'addi') and src is not None:
                # shift the const anchor; keep base-ness (index still unknown)
                setreg(ins.rt, (src[0], (src[1] + ins.simm) & 0xFFFFFFFF))
            else:
                setreg(ins.rt, None)          # andi/slti/... -> not a clean base
        elif k == 'rarith' and ins.mnemonic in ('addu', 'add', 'daddu', 'dadd',
                                                 'or'):
            sv, tv = state.get(ins.rs), state.get(ins.rt)
            # $zero contributes nothing; count non-zero anchored sources.
            anchors = []
            for r, v in ((ins.rs, sv), (ins.rt, tv)):
                if r != 0 and v is not None:
                    anchors.append(v[1])
            if len(anchors) == 1:
                # exactly one lui-const-derived source -> dest is a table base
                # (covers `addu at,at,gid` and `or at,zero,const` copy forms)
                setreg(ins.rd, ('base', anchors[0]))
            else:
                setreg(ins.rd, None)
        else:
            d = ins.dest_reg()
            if d is not None:
                setreg(d, None)               # any other write clobbers tracking

    return out


# ---------------------------------------------------------------------------
# Address book
# ---------------------------------------------------------------------------
def address_book(reloc):
    """The set of VAs a cave is allowed to touch absolutely, derived FROM the
    relocation single-source so it tracks the real table VAs.
        {ADV_VA, LSH_VA, ADV2_VA, LSH2_VA, mode sentinel 0x4FED18}"""
    return {
        reloc.ADV_VA,
        reloc.LSH_VA,
        reloc.ADV2_VA,
        reloc.LSH2_VA,
        MODE_SENTINEL_VA,
    }


def check_effective_addresses(insns, book, expected=None):
    """For every recorded absolute access assert EA in `book`.  If `expected`
    (an iterable of VAs) is given, also assert the SET of *read* EAs equals it.
    Returns a list of failure dicts (empty == pass)."""
    accesses = resolve_absolute_accesses(insns)
    failures = []
    for a in accesses:
        if a['ea'] not in book:
            failures.append({
                'va': a['va'],
                'kind': a['kind'],
                'mnemonic': a['mnemonic'],
                'ea': a['ea'],
                'imm': a['imm'],
                'base_reg': a['base_reg'],
                'msg': ("%s @0x%06X computes EA 0x%06X (base %s + sext16(0x%04X)) "
                        "-- NOT in the address book %s"
                        % (a['mnemonic'], a['va'], a['ea'], rname(a['base_reg']),
                           a['imm'], sorted('0x%06X' % v for v in book))),
            })
    if expected is not None:
        want = set(expected)
        got = set(a['ea'] for a in accesses if a['kind'] == 'load')
        if got != want:
            failures.append({
                'va': None, 'kind': 'expected-set', 'mnemonic': None,
                'ea': None, 'imm': None, 'base_reg': None,
                'msg': ("read-EA set %s != expected %s"
                        % (sorted('0x%06X' % v for v in got),
                           sorted('0x%06X' % v for v in want))),
            })
    return failures


# ---------------------------------------------------------------------------
# RULE K -- ban k0/k1; warn on t9/gp
# ---------------------------------------------------------------------------
def check_no_kernel_regs(insns):
    """RULE K.  Returns (failures, warnings).

    failures: any insn that references k0(26) or k1(27) in a field it actually
              uses -> {va, reg, reg_name, mnemonic, text}.
    warnings: any insn referencing t9(25) or gp(28) (legitimate for .cpload /
              PIC / global-pointer but 'needs an explicit justification')."""
    failures, warnings = [], []
    for ins in insns:
        used = ins.used_regs()
        for r in sorted(used):
            if r in (K0, K1):
                failures.append({
                    'va': ins.va, 'reg': r, 'reg_name': rname(r),
                    'mnemonic': ins.mnemonic, 'text': ins.text(),
                    'msg': ("%s @0x%06X uses KERNEL-live $%s (reg %d) -- k0/k1 are "
                            "trashed by async interrupts; RULE K violation"
                            % (ins.mnemonic, ins.va, rname(r), r)),
                })
            elif r in (T9, GP):
                warnings.append({
                    'va': ins.va, 'reg': r, 'reg_name': rname(r),
                    'mnemonic': ins.mnemonic, 'text': ins.text(),
                    'msg': ("%s @0x%06X uses $%s (reg %d) -- needs justification "
                            "(t9=PIC .cpload / gp=global ptr)"
                            % (ins.mnemonic, ins.va, rname(r), r)),
                })
    return failures, warnings


# ---------------------------------------------------------------------------
# Optional capstone cross-validation (NOT a gate; diagnostics only)
# ---------------------------------------------------------------------------
def capstone_crosscheck(words, base_va):
    """Best-effort mnemonic cross-check vs capstone.  Returns a list of
    (va, our_text, capstone_text) rows or None if capstone is unavailable.
    The gate NEVER depends on this (R5900-specific ops may not decode)."""
    try:
        import capstone
    except Exception:
        return None
    import struct as _s
    md = capstone.Cs(capstone.CS_ARCH_MIPS,
                     capstone.CS_MODE_MIPS64 | capstone.CS_MODE_LITTLE_ENDIAN)
    blob = b"".join(_s.pack("<I", w & 0xFFFFFFFF) for w in words)
    cap = {}
    for insn in md.disasm(blob, base_va):
        cap[insn.address] = ("%s %s" % (insn.mnemonic, insn.op_str)).strip()
    rows = []
    for ins in decode(words, base_va):
        rows.append((ins.va, ins.text(), cap.get(ins.va, "<capstone: none>")))
    return rows


# ---------------------------------------------------------------------------
# Standalone report
# ---------------------------------------------------------------------------
def _report_cave(name, words, base_va, book):
    print("=== %s @0x%06X (%d words) ===" % (name, base_va, len(words)))
    insns = decode(words, base_va)
    for ins in insns:
        print("  0x%06X  %08X  %s" % (ins.va, ins.word, ins.text()))
    accesses = resolve_absolute_accesses(insns)
    for a in accesses:
        tag = "OK " if a['ea'] in book else "BAD"
        print("    [%s] abs %s -> EA 0x%06X (base %s, %s)"
              % (tag, a['mnemonic'], a['ea'], rname(a['base_reg']), a['base_kind']))
    fails, warns = check_no_kernel_regs(insns)
    for f in fails:
        print("    [RULE-K FAIL] " + f['msg'])
    for w in warns:
        print("    [rule-k warn] " + w['msg'])


if __name__ == '__main__':
    import os
    import sys
    try:
        sys.stdout.reconfigure(encoding='ascii', errors='replace')
    except Exception:
        pass
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    '..', 'build'))
    import _reloc_v147_design as RELOC
    book = address_book(RELOC)
    print("ADDRESS BOOK:", sorted('0x%06X' % v for v in book))
    for nm, ws, va in [
        ("P27", RELOC.P27_WORDS, RELOC.P27_VA),
        ("P14c1", RELOC.P14C1_WORDS, RELOC.P14C1_VA),
        ("P14c2", RELOC.P14C2_WORDS, RELOC.P14C2_VA),
        ("P29f1", RELOC.P29_F1_WORDS, RELOC.P29_F1_VA),
        ("P29f2", RELOC.P29_F2_WORDS, RELOC.P29_F2_VA),
        ("P31f1", RELOC.P31_F1_WORDS, RELOC.P31_F1_VA),
        ("P31f2", RELOC.P31_F2_WORDS, RELOC.P31_F2_VA),
    ]:
        _report_cave(nm, ws, va, book)
