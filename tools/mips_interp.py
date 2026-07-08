"""Tiny EE-MIPS (o32) interpreter for STATIC shrink-equivalence verification.

Purpose: execute a small self-contained leaf routine (our replacement strncpy,
and the ORIGINAL routine's scalar tail) over a sandbox memory + register file so
tests/test_shrink_equivalence.py can prove a shrunk replacement is behaviourally
identical to the original BEFORE any build/boot.

Scope: the integer/scalar opcode subset those routines use. It HARD-TRAPS on
anything outside that subset (jal/jalr/syscall/mult/div, unmapped memory access,
or an instruction-budget overrun) so a routine that strays is caught, never
silently mis-executed.  Delay slots (branch + branch-likely nullification) are
modelled explicitly.  This is a verification oracle, not a full PS2 emulator.

Registers are 64-bit (PS2 EE); we keep them as Python ints masked to 64 bits and
sign/zero-extend on the 32-bit ops we implement (addiu/addu/sltu... EE keeps 32-bit
results sign-extended into 64).  For strncpy the only 64-bit op is `daddu rd,rs,zero`
(a register move), which we implement exactly.
"""

MASK64 = (1 << 64) - 1
MASK32 = (1 << 32) - 1


class Trap(Exception):
    pass


def s32(v):
    v &= MASK32
    return v - (1 << 32) if v & 0x80000000 else v


def s16(v):
    v &= 0xFFFF
    return v - (1 << 16) if v & 0x8000 else v


class Mem:
    """Byte-addressed sandbox. Any access outside a declared region traps."""
    def __init__(self):
        self.regions = []   # list of (lo, bytearray)

    def add(self, base, data):
        self.regions.append((base, bytearray(data)))
        return base

    def _find(self, addr, n):
        for lo, buf in self.regions:
            if lo <= addr and addr + n <= lo + len(buf):
                return buf, addr - lo
        raise Trap("unmapped access @0x%X (n=%d)" % (addr, n))

    def load(self, addr, n, signed):
        buf, off = self._find(addr, n)
        v = int.from_bytes(buf[off:off + n], "little")
        if signed and v & (1 << (8 * n - 1)):
            v -= 1 << (8 * n)
        return v

    def store(self, addr, n, val):
        buf, off = self._find(addr, n)
        buf[off:off + n] = (val & ((1 << (8 * n)) - 1)).to_bytes(n, "little")

    def snapshot(self):
        return [(lo, bytes(buf)) for lo, buf in self.regions]


def run(code_base, code_bytes, mem, regs, entry, max_insns=100000):
    """Execute from `entry` until `jr ra`. regs: dict name->int (a0..a3, sp, ra...).
    Returns the value in v0. Traps on out-of-subset ops / unmapped mem / runaway."""
    import struct
    RN = ['zero', 'at', 'v0', 'v1', 'a0', 'a1', 'a2', 'a3', 't0', 't1', 't2', 't3',
          't4', 't5', 't6', 't7', 's0', 's1', 's2', 's3', 's4', 's5', 's6', 's7',
          't8', 't9', 'k0', 'k1', 'gp', 'sp', 'fp', 'ra']
    r = [0] * 32
    for k, v in regs.items():
        r[RN.index(k)] = v & MASK64

    def fetch(pc):
        o = pc - code_base
        if o < 0 or o + 4 > len(code_bytes):
            raise Trap("fetch outside routine @0x%X" % pc)
        return struct.unpack_from("<I", code_bytes, o)[0]

    RA = 0x0BADF00D            # sentinel: jr ra with ra==this ends the run
    r[31] = regs.get('ra', RA) & MASK64
    ret_marker = r[31]

    pc = entry
    budget = max_insns
    while True:
        budget -= 1
        if budget <= 0:
            raise Trap("instruction budget exceeded (runaway loop)")
        w = fetch(pc)
        op = w >> 26
        rs = (w >> 21) & 31
        rt = (w >> 16) & 31
        rd = (w >> 11) & 31
        sa = (w >> 6) & 31
        fn = w & 0x3F
        imm = w & 0xFFFF
        npc = pc + 4
        branch = None      # (target, likely)

        if w == 0:                                    # nop
            pass
        elif op == 0:                                 # SPECIAL
            if fn == 0x08:                            # jr
                if rs == 31 and r[31] == ret_marker:
                    ds = fetch(npc)                   # jr's delay slot runs before return
                    _step_simple(ds, r, mem, npc)
                    r[0] = 0
                    return s32(r[2])                  # jr ra -> done, return v0
                raise Trap("jr to non-ra @0x%X" % pc)
            elif fn == 0x09:
                raise Trap("jalr (call) @0x%X -- not a leaf" % pc)
            elif fn == 0x2D:                          # daddu (used as 64-bit move)
                r[rd] = (r[rs] + r[rt]) & MASK64
            elif fn == 0x21:                          # addu
                r[rd] = s32(r[rs] + r[rt]) & MASK64
            elif fn == 0x23:                          # subu
                r[rd] = s32(r[rs] - r[rt]) & MASK64
            elif fn == 0x25:                          # or
                r[rd] = r[rs] | r[rt]
            elif fn == 0x24:                          # and
                r[rd] = r[rs] & r[rt]
            elif fn == 0x27:                          # nor
                r[rd] = (~(r[rs] | r[rt])) & MASK64
            elif fn == 0x2A:                          # slt
                r[rd] = 1 if s32(r[rs]) < s32(r[rt]) else 0
            elif fn == 0x2B:                          # sltu
                r[rd] = 1 if (r[rs] & MASK32) < (r[rt] & MASK32) else 0
            elif fn == 0x00:                          # sll
                r[rd] = s32((r[rt] << sa) & MASK32) & MASK64
            elif fn == 0x02:                          # srl
                r[rd] = s32((r[rt] & MASK32) >> sa) & MASK64
            elif fn == 0x03:                          # sra
                r[rd] = s32(s32(r[rt]) >> sa) & MASK64
            elif fn == 0x0A:                          # movz
                if r[rt] == 0:
                    r[rd] = r[rs]
            elif fn == 0x0B:                          # movn
                if r[rt] != 0:
                    r[rd] = r[rs]
            else:
                raise Trap("unsupported SPECIAL fn=0x%02x @0x%X" % (fn, pc))
        elif op == 0x09:                              # addiu
            r[rt] = s32(r[rs] + s16(imm)) & MASK64
        elif op == 0x0C:                              # andi
            r[rt] = r[rs] & imm
        elif op == 0x0D:                              # ori
            r[rt] = r[rs] | imm
        elif op == 0x0E:                              # xori
            r[rt] = r[rs] ^ imm
        elif op == 0x0F:                              # lui
            r[rt] = s32((imm << 16) & MASK32) & MASK64
        elif op == 0x0A:                              # slti
            r[rt] = 1 if s32(r[rs]) < s16(imm) else 0
        elif op == 0x0B:                              # sltiu
            r[rt] = 1 if (r[rs] & MASK32) < (s16(imm) & MASK32) else 0
        elif op == 0x24:                              # lbu
            r[rt] = mem.load((r[rs] + s16(imm)) & MASK32, 1, False)
        elif op == 0x20:                              # lb
            r[rt] = s32(mem.load((r[rs] + s16(imm)) & MASK32, 1, True)) & MASK64
        elif op == 0x28:                              # sb
            mem.store((r[rs] + s16(imm)) & MASK32, 1, r[rt])
        elif op == 0x25:                              # lhu
            r[rt] = mem.load((r[rs] + s16(imm)) & MASK32, 2, False)
        elif op == 0x29:                              # sh
            mem.store((r[rs] + s16(imm)) & MASK32, 2, r[rt])
        elif op == 0x23:                              # lw
            r[rt] = s32(mem.load((r[rs] + s16(imm)) & MASK32, 4, True)) & MASK64
        elif op == 0x2B:                              # sw
            mem.store((r[rs] + s16(imm)) & MASK32, 4, r[rt])
        elif op in (0x04, 0x05, 0x14, 0x15):          # beq/bne/beql/bnel
            take = (r[rs] == r[rt]) if op in (0x04, 0x14) else (r[rs] != r[rt])
            branch = (pc + 4 + s16(imm) * 4, op in (0x14, 0x15), take)
        elif op in (0x06, 0x07, 0x16, 0x17):          # blez/bgtz/blezl/bgtzl
            v = s32(r[rs])
            take = (v <= 0) if op in (0x06, 0x16) else (v > 0)
            branch = (pc + 4 + s16(imm) * 4, op in (0x16, 0x17), take)
        elif op == 0x01:                              # REGIMM bltz/bgez(l)
            v = s32(r[rs])
            take = (v < 0) if rt in (0, 2) else (v >= 0)
            branch = (pc + 4 + s16(imm) * 4, rt in (2, 3), take)
        elif op == 0x03:
            raise Trap("jal (call) @0x%X -- not a leaf" % pc)
        elif op == 0x02:
            raise Trap("j @0x%X -- outside verification scope" % pc)
        else:
            raise Trap("unsupported opcode 0x%02x @0x%X" % (op, pc))

        r[0] = 0
        if branch is None:
            pc = npc
            continue
        target, likely, take = branch
        if likely and not take:
            pc = npc + 4          # branch-likely not taken -> nullify delay slot
            continue
        # execute the delay-slot instruction (one non-branch insn), then jump
        ds = fetch(npc)
        _step_simple(ds, r, mem, npc)
        r[0] = 0
        pc = target if take else npc + 4


def _step_simple(w, r, mem, pc):
    """Execute ONE non-control instruction (a delay-slot insn). Traps on control
    flow in a delay slot (not used by our routines)."""
    op = w >> 26
    rs = (w >> 21) & 31
    rt = (w >> 16) & 31
    rd = (w >> 11) & 31
    sa = (w >> 6) & 31
    fn = w & 0x3F
    imm = w & 0xFFFF
    if w == 0:
        return
    if op == 0:
        if fn == 0x2D:
            r[rd] = (r[rs] + r[rt]) & MASK64
        elif fn == 0x21:
            r[rd] = s32(r[rs] + r[rt]) & MASK64
        elif fn == 0x25:
            r[rd] = r[rs] | r[rt]
        elif fn == 0x24:
            r[rd] = r[rs] & r[rt]
        elif fn == 0x00:
            r[rd] = s32((r[rt] << sa) & MASK32) & MASK64
        else:
            raise Trap("unsupported delay-slot SPECIAL fn=0x%02x @0x%X" % (fn, pc))
        return
    if op == 0x09:
        r[rt] = s32(r[rs] + s16(imm)) & MASK64
    elif op == 0x0F:
        r[rt] = s32((imm << 16) & MASK32) & MASK64
    elif op == 0x0D:
        r[rt] = r[rs] | imm
    elif op == 0x24:
        r[rt] = mem.load((r[rs] + s16(imm)) & MASK32, 1, False)
    elif op == 0x28:
        mem.store((r[rs] + s16(imm)) & MASK32, 1, r[rt])
    elif op == 0x23:
        r[rt] = s32(mem.load((r[rs] + s16(imm)) & MASK32, 4, True)) & MASK64
    elif op == 0x2B:
        mem.store((r[rs] + s16(imm)) & MASK32, 4, r[rt])
    else:
        raise Trap("unsupported delay-slot opcode 0x%02x @0x%X" % (op, pc))
    r[0] = 0
