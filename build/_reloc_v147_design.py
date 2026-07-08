#!/usr/bin/env python3
"""
v147 battle-fix relocation design + verification (standalone) -- SIMPLIFIED.

ROOT GOAL: the box renderer 0x3A2EF0 hooks `j` into Patch-27's proportional cave.
In production that cave lived at VA 0x4C7410, INSIDE the EE battle-heap arena
(0x4B0E00..0x4FDE30).  During SOME battle phases the heap stomps that RAM ->
`j 0x4C7410` jumps into garbage -> battle aborts / no monsters.

EMPIRICAL PROOF (battle .p2s dumps, this build):
  * P27 cave @0x4C7410  : STOMPED in battlebreak / fightsoftlock dumps
                          (word0 0x3C030050 -> 0x3C010050), INTACT in emptybattle/fuckshit.
  * P14 cave1 @0x4C7540 : INTACT across ALL battle dumps.
  * P14 cave2 @0x4C7670 : INTACT across ALL battle dumps.
  * Canonical ADV table @0x4C7564 / LSH @0x4C7690 : INTACT across ALL dumps
                          (title + battle), so a relocated cave can read them safely.

=> ONLY Patch-27's cave is battle-traversed AND stompable.  Patch-14 is NOT.

THE FIX (minimal):
  Relocate ONLY the Patch-27 cave out of the arena, into verified-safe code-segment
  padding (GAP_P27 @0x4AB554, pad after a `jr ra` epilogue, genuinely zero in pristine
  AND in every live dump).  Keep the cave BYTE-FAITHFUL to production (it reads the
  CANONICAL 256-byte ADV table at lbu 0x7564(0x4C0000) -- NO table relocation, NO
  95-byte shrink, NO ASCII guard).  Only the cave's own base address + its hook's
  j-target change.

WHAT IS *NOT* TOUCHED (this is why the v146/v147 title-hang risk is gone):
  * Patch-14 caves stay IN-ARENA at 0x4C7540 / 0x4C7670 (production layout).
  * The gate marker @file 0x209820 (VA 0x3097A0) stays the PRODUCTION value
    0x08131D50 (= j 0x4C7540).  Dependent patches 19/24/25/26/27 gate on it unchanged.
  * The ADV/LSH tables stay at canonical 0x4C7564 / 0x4C7690.  NOTHING is written into
    the PsII libgraph SDK data block at 0x4AF2E0..0x4AF337 (the prior v147 relocated the
    ADV table to 0x4AF336 and smeared the high 2 bytes of the final libgraph GS-write
    descriptor word 0x4AF334=0x000002FF -> the title-screen hang).

Run:  python build/_reloc_v147_design.py
It PRINTS the design + a self-check; it does NOT modify the EXE.  patch_exe.py imports
the resulting word lists / addresses from here so there is ONE source.
"""

# ------------------------------------------------------------------ assembler
def _R(n):
    m = {'zero':0,'at':1,'v0':2,'v1':3,'a0':4,'a1':5,'a2':6,'a3':7,'t0':8,'t1':9,
         't2':10,'t3':11,'t4':12,'t5':13,'t6':14,'t7':15,'s0':16,'s1':17,'s2':18,
         's3':19,'s4':20,'s5':21,'s6':22,'s7':23,'t8':24,'t9':25,'k0':26,'k1':27,
         'gp':28,'sp':29,'s8':30,'ra':31}
    return m[n]

def lui(rt, imm):        return (0x0f << 26) | (_R(rt) << 16) | (imm & 0xffff)
def lw(rt, off, rs):     return (0x23 << 26) | (_R(rs) << 21) | (_R(rt) << 16) | (off & 0xffff)
def lh(rt, off, rs):     return (0x21 << 26) | (_R(rs) << 21) | (_R(rt) << 16) | (off & 0xffff)
def lhu(rt, off, rs):    return (0x25 << 26) | (_R(rs) << 21) | (_R(rt) << 16) | (off & 0xffff)
def lbu(rt, off, rs):    return (0x24 << 26) | (_R(rs) << 21) | (_R(rt) << 16) | (off & 0xffff)
def sh(rt, off, rs):     return (0x29 << 26) | (_R(rs) << 21) | (_R(rt) << 16) | (off & 0xffff)
def addiu(rt, rs, imm):  return (0x09 << 26) | (_R(rs) << 21) | (_R(rt) << 16) | (imm & 0xffff)
def andi(rt, rs, imm):   return (0x0c << 26) | (_R(rs) << 21) | (_R(rt) << 16) | (imm & 0xffff)
def sltiu(rt, rs, imm):  return (0x0b << 26) | (_R(rs) << 21) | (_R(rt) << 16) | (imm & 0xffff)
def addu(rd, rs, rt):    return (_R(rs) << 21) | (_R(rt) << 16) | (_R(rd) << 11) | 0x21
def subu(rd, rs, rt):    return (_R(rs) << 21) | (_R(rt) << 16) | (_R(rd) << 11) | 0x23
def daddu(rd, rs, rt):   return (_R(rs) << 21) | (_R(rt) << 16) | (_R(rd) << 11) | 0x2d
def sb(rt, off, rs):     return (0x28 << 26) | (_R(rs) << 21) | (_R(rt) << 16) | (off & 0xffff)
def dsll32(rd, rt, sa):  return (_R(rt) << 16) | (_R(rd) << 11) | ((sa & 31) << 6) | 0x3c
def dsra32(rd, rt, sa):  return (_R(rt) << 16) | (_R(rd) << 11) | ((sa & 31) << 6) | 0x3f
def srl(rd, rt, sa):     return (_R(rt) << 16) | (_R(rd) << 11) | ((sa & 31) << 6) | 0x02
def beq(rs, rt, tgt, pc):return (0x04 << 26) | (_R(rs) << 21) | (_R(rt) << 16) | (((tgt - (pc + 4)) >> 2) & 0xffff)
def bne(rs, rt, tgt, pc):return (0x05 << 26) | (_R(rs) << 21) | (_R(rt) << 16) | (((tgt - (pc + 4)) >> 2) & 0xffff)
def beqz(rs, tgt, pc):   return beq(rs, 'zero', tgt, pc)
def b(tgt, pc):          return beq('zero', 'zero', tgt, pc)
def j(va):               return (0x02 << 26) | ((va >> 2) & 0x3ffffff)
def jal(va):             return (0x03 << 26) | ((va >> 2) & 0x3ffffff)
def jr(rs):              return (_R(rs) << 21) | 0x08
def movn(rd, rs, rt):    return (_R(rs) << 21) | (_R(rt) << 16) | (_R(rd) << 11) | 0x0b
def movz(rd, rs, rt):    return (_R(rs) << 21) | (_R(rt) << 16) | (_R(rd) << 11) | 0x0a
def nop():               return 0

# ------------------------------------------------------------------ addresses
# EE: eeMemory[VA] == VA.  EXE file_off = VA - 0x100000 + 0x80.
# Battle-heap arena = 0x4B0E00..0x4FDE30 (the P27 cave MUST be moved out of it).
#
# Verified-safe CODE-SEGMENT gap for the relocated P27 cave:
#   GAP_P27   0x4AB554 len 175  (pad after a function epilogue `jr ra; addiu sp,sp,0x50`).
#             Pristine-zero AND zero in every live dump (title + 4 battle + chargen +
#             request); the bytes just before are a real function epilogue, not a heap hole.
#
# CANONICAL tables stay where production wrote them (Patch 14, in patch_exe.py):
#   ADV  @VA 0x4C7564  (lbu 0x7564(0x4C0000))   -- intact across all dumps
#   LSH  @VA 0x4C7690  (lbu 0x7690(0x4C0000))   -- intact across all dumps
# The relocated P27 cave reads the canonical ADV table DIRECTLY, exactly like production.
P27_VA   = 0x4AB554          # relocated Patch-27 box-text cave (20 words / 80B)

# Patch-14 caves are NOT relocated -- they ship at the production in-arena addresses,
# which are never heap-stomped (proven).  We still EXPORT their word lists + VAs so
# patch_exe's Patch-14 installer is a single-source consumer (it writes them in-arena).
P14C1_VA = 0x4C7540          # Patch-14 advance-LUT cave (production in-arena)
P14C2_VA = 0x4C7670          # Patch-14 draw-shift cave  (production in-arena)
# ── v174 EXE-EXTENSION: font metric tables moved OUT of the battle arena ──────
# The v173 tables sat at the in-arena rodata holes 0x4C7564/0x4C7690.  Even though
# those were proven "intact" in dumps, the FINAL battle fix requires the arena
# (0x4B0E00..0x4FDE30) to ship byte-identical to pristine.  v174 relocates the
# three load-bearing tables into a NEW file-backed PT_LOAD (repurposed PH1) at a
# heap-reserved VA 0x580000 (64KiB-aligned so every cave lbu offset is <0x8000 ->
# no sign-extension carry).  patch_exe writes the 768B blob at file 0x3FDD00 and
# bumps the sbrk break so malloc can never hand back an address inside the segment.
#   ADV_VA  0x580000  adv_table_256      (R1188 advance,   Patch14/19 readers)
#   LSH_VA  0x580100  leftshift_table_256(R1188 leftshift, Patch14/19/29/31 readers)
#   ADV2_VA 0x580200  adv2_table_256     (R2100 chargen advance, Patch26/27/25 readers)
# v175 FIX B + Option E (the R2100 chargen-leftshift restore -- the "holy fix"):
# FOUR metric tables live in the FREED strncpy span -- ZERO ELF-structure change
# (the v174 PT_LOAD @0x580000 boots to BIOS; a clean LIEF-added segment crashes
# PCSX2).  We shrink the self-contained libc strncpy @0x121568 (444B -> 76B; proven
# byte-for-byte equivalent by tests/test_shrink_equivalence.py, dual-oracle) and pack
# FOUR 92-byte tables into the 368B freed tail: 4*92 = 368 EXACTLY.  gids 0..91 cover
# all real text (chargen/dialogue gid = char-0x20; max glyph 'z' = 90; dropped 92..94
# = '|}~' never appear).  All VAs low-16 < 0x8000 (no lbu sign-ext); ~3.7MB below the
# arena in pure .text.  ARENA ships byte-identical to pristine.  Tales-of-Rebirth
# slps.asm precedent (c:\temp).
#   ADV_VA  adv_table_256        R1188 dialogue advance   (P14c1/P19c1)
#   LSH_VA  leftshift_table_256  R1188 dialogue leftshift (P14c2/P19c2)
#   ADV2_VA adv2_table_256       R2100 chargen advance    (P26/P27)
#   LSH2_VA leftshift2_table_256 R2100 chargen leftshift  (P29/P31)  <- the deferred
#     4th table, NOW SHIPPED.  v174 gave chargen the tight R2100 ADVANCE but left LSH2
#     aliased to the wide R1188 leftshift -> draw-X = pen - R1188_lsh yanked glyphs
#     past the small pen advance (the "worse than ever" blow-out).  Shipping the
#     matched R2100 leftshift restores the upright font clean.
STRNCPY_VA   = 0x121568          # reclaimed libc strncpy (leaf, no gp/abs-addr, 12 callers)
STRNCPY_FILE = STRNCPY_VA - 0x100000 + 0x80   # 0x215E8
STRNCPY_ORIG_LEN = 444
TABLE_ENTRIES = 92               # 4*92 = 368 = the freed span; gids 0..91 (max real 'z'=90)
ADV_VA   = 0x1215B4                     # freed span +0x00
LSH_VA   = ADV_VA  + TABLE_ENTRIES      # 0x121610  freed span +0x5C
ADV2_VA  = LSH_VA  + TABLE_ENTRIES      # 0x12166C  freed span +0xB8
LSH2_VA  = ADV2_VA + TABLE_ENTRIES      # 0x1216C8  freed span +0x114 (R2100 chargen LSH)


def build_strncpy_replacement(base=STRNCPY_VA):
    """Compact scalar strncpy (a0=dst, a1=src, a2=n -> v0=dst): 76B / 19 instrs.
    VERIFIED byte-for-byte equivalent to the original @0x121568 by
    tests/test_shrink_equivalence.py (dual-oracle, 2008 cases). SINGLE SOURCE:
    both the gate and patch_exe consume this so the test proves the shipped bytes."""
    import struct
    COPY, PAD, DONE = base + 1 * 4, base + 10 * 4, base + 17 * 4
    w = [
        daddu('t0', 'a0', 'zero'),               # 0   t0 = dst (return)
        beq('a2', 'zero', DONE, base + 1 * 4),   # 1   COPY: n==0 -> done
        nop(),                                    # 2
        lbu('v0', 0, 'a1'),                      # 3   v0 = *src
        addiu('a1', 'a1', 1),                    # 4   src++
        sb('v0', 0, 'a0'),                       # 5   *dst = v0
        addiu('a0', 'a0', 1),                    # 6   dst++
        addiu('a2', 'a2', -1),                   # 7   n--
        bne('v0', 'zero', COPY, base + 8 * 4),   # 8   v0!=0 -> keep copying
        nop(),                                    # 9
        beq('a2', 'zero', DONE, base + 10 * 4),  # 10  PAD: n==0 -> done
        nop(),                                    # 11
        sb('zero', 0, 'a0'),                     # 12  *dst = 0
        addiu('a0', 'a0', 1),                    # 13
        addiu('a2', 'a2', -1),                   # 14
        b(PAD, base + 15 * 4),                   # 15  -> PAD
        nop(),                                    # 16
        jr('ra'),                                # 17  DONE
        daddu('v0', 't0', 'zero'),               # 18  (delay) v0 = dst
    ]
    return b''.join(struct.pack('<I', x) for x in w)


def build_metric_tables():
    """The FOUR 92-byte tables in VA order: [(va, bytes)]. Single source.
    ADV/LSH = R1188 dialogue advance/leftshift; ADV2/LSH2 = R2100 chargen
    advance/leftshift (Option E: the matched R2100 pair fixes the half-done
    ADV2 restore).  4*92 = 368 = the freed span; gids 0..91 cover all real text."""
    import glyph_metrics as gm
    n = TABLE_ENTRIES
    tabs = [(ADV_VA, gm.adv_table_256()),
            (LSH_VA, gm.leftshift_table_256()),
            (ADV2_VA, gm.adv2_table_256()),
            (LSH2_VA, gm.leftshift2_table_256())]
    return [(va, bytes(t[:n])) for va, t in tabs]

ARENA_LO, ARENA_HI = 0x4B0E00, 0x4FDE30

# Rejoin target for the P27 cave (UNCHANGED -- points back into the renderer)
P27_REJOIN  = 0x3A31B8

def jword(va):  return j(va)

def fo(va):     return va - 0x100000 + 0x80


# ------------------------------------------------------------------ P27 cave (RELOCATED, R2100 table)
# Structurally BYTE-FAITHFUL to the production cave that lived @0x4C7410 (recovered
# from the v144 battle dump); the base address (0x4C7410 -> P27_VA), the internal `b`
# target, and (v158) the TABLE READ change.  v158: the 0x3A2EF0 renderer draws the
# R2100 sub0 UPRIGHT 16px font in BOTH gated modes (5 chargen / 7 request -- verified
# from live screenshots).  v173 BATTLE-FIX: the PROP arm now reads the CANONICAL R1188
# ADV @0x4C7564 (lui 0x4C / lbu 0x7564) -- the R2100 in-arena table was DROPPED because it
# softlocked battle at every placement (see the ADV2_VA block).  Chargen reverts to the
# mild pre-v158 spacing; the canonical table is intact in every battle dump.  Still no
# ASCII guard -- the 256B table covers gid 0..94 (all English glyphs); gid>=95 never occurs
# and reads an adjacent tail byte (cosmetic):
#   lui v1,0x50 ; lw v1,-0x12E8(v1)  (mode) ; addiu v1,v1,-5 ; beqz v1->PROP ;
#   addiu v1,v1,-2 (ds) ; beqz v1->PROP ; nop ;
#   STOCK: lw v1,0xD0(sp) ; dsll32 v1,16 ; dsra32 v1,16 ; b APPLY ; nop ;
#   PROP : lbu v1,-1(s2) ; lui at,0x4C ; addu at,at,v1 ; lbu v1,0x7564(at) ;
#   APPLY: addu v1,s1,v1 ; dsll32 s1,16 ; dsra32 s1,16 ; j 0x3A31B8 ; nop
def build_p27():
    base = P27_VA
    w = []
    def at(i): return base + i * 4
    w.append(lui('v1', 0x50))                 # 0  lui v1,0x50
    w.append(lw('v1', -0x12E8, 'v1'))         # 1  lw v1,-0x12E8(v1)  ; mode (RAM 0x4FED18)
    w.append(addiu('v1', 'v1', -5))           # 2  addiu v1,v1,-5   ; ==5 chargen?
    i_b1 = 3; w.append(0)                      # 3  beqz v1,PROP   (patch)
    w.append(addiu('v1', 'v1', -2))           # 4  (ds) addiu v1,v1,-2  ; ==7 request?
    i_b2 = 5; w.append(0)                      # 5  beqz v1,PROP   (patch)
    w.append(nop())                           # 6  (ds) nop
    # STOCK arm (mode != 5 and != 7 -> original monospace pitch path, register-faithful)
    w.append(lw('v1', 0xD0, 'sp'))            # 7  lw v1,0xD0(sp)   ; original pitch
    w.append(dsll32('v1', 'v1', 16))          # 8
    w.append(dsra32('v1', 'v1', 16))          # 9
    i_bs = 10; w.append(0)                     # 10 b APPLY        (patch)
    w.append(nop())                           # 11 (ds)
    # PROP arm (chargen/request -> proportional advance from the R2100 ADV2 table)
    i_prop = len(w)
    w.append(lbu('v1', -1, 's2'))             # 12 lbu v1,-1(s2)   ; gid (char-32, <95)
    w.append(lui('at', ADV2_VA >> 16))        # 13 lui at,hi(ADV2) ; v174: R2100 ADV2 table base
    w.append(addu('at', 'at', 'v1'))          # 14 addu at,at,v1
    w.append(lbu('v1', ADV2_VA & 0xFFFF, 'at'))  # 15 lbu v1,lo(ADV2)(at) ; ADV2[gid] @segment
    # APPLY
    i_apply = len(w)
    w.append(addu('v1', 's1', 'v1'))          # 16 addu v1,s1,v1
    w.append(dsll32('s1', 'v1', 16))          # 17
    w.append(dsra32('s1', 's1', 16))          # 18
    w.append(j(P27_REJOIN))                   # 19 j 0x3A31B8
    w.append(nop())                           # 20 (ds)  (only emitted if a branch needs it; see below)
    # NOTE: the production cave was 20 words (indices 0..19); the trailing nop above keeps
    # the delay slot of the final `j`.  Patch the placeholders:
    w[i_b1] = beqz('v1', at(i_prop), at(i_b1))
    w[i_b2] = beqz('v1', at(i_prop), at(i_b2))
    w[i_bs] = b(at(i_apply), at(i_bs))
    return w


# ------------------------------------------------------------------ P14 caves (PRODUCTION in-arena, NOT relocated)
# These are the ORIGINAL production caves (recovered byte-for-byte from the v144 dump),
# read the canonical tables, and ship at their in-arena addresses (never heap-stomped).
# patch_exe writes them exactly where production did; the gate marker stays 0x08131D50.
def build_p14c1():
    # @0x4C7540: lui t0,0x4C ; andi v1,s1,0xFF ; addu t0,t0,v1 ; lbu v1,0x7564(t0) ;
    #            lh v0,0x1CE(sp) ; addu v0,v0,v1 ; sh v0,0x1CE(sp) ; j 0x3097E0 ; nop
    return [
        lui('t0', ADV_VA >> 16),              # 0  v174: R1188 ADV table base (segment)
        andi('v1', 's1', 0xFF),               # 1
        addu('t0', 't0', 'v1'),               # 2
        lbu('v1', ADV_VA & 0xFFFF, 't0'),     # 3  ADV[gid] @segment
        lh('v0', 0x1CE, 'sp'),                # 4
        addu('v0', 'v0', 'v1'),               # 5
        sh('v0', 0x1CE, 'sp'),                # 6
        j(0x3097E0),                          # 7
        nop(),                                # 8
    ]

def build_p14c2():
    # @0x4C7670: lui at,0x4C ; addu at,at,s1 ; lbu at,0x7690(at) ; subu a3,a3,at ;
    #            addu t4,a3,t4 ; j 0x309758 ; nop
    return [
        lui('at', LSH_VA >> 16),              # 0  v174: R1188 LSH table base (segment)
        addu('at', 'at', 's1'),               # 1
        lbu('at', LSH_VA & 0xFFFF, 'at'),     # 2  LSH[gid] @segment
        subu('a3', 'a3', 'at'),               # 3
        addu('t4', 'a3', 't4'),               # 4
        j(0x309758),                          # 5
        nop(),                                # 6
    ]


P27_WORDS   = build_p27()
P14C1_WORDS = build_p14c1()
P14C2_WORDS = build_p14c2()

# new hook j-words
P27_HOOK_JWORD   = jword(P27_VA)      # j 0x4AB554 (RELOCATED)
P14_HOOK1_JWORD  = jword(P14C1_VA)    # j 0x4C7540 (production in-arena = 0x08131D50)
P14_HOOK2_JWORD  = jword(P14C2_VA)    # j 0x4C7670 (production in-arena = 0x08131D9C)
# Dependent patches 19/24/25/26/27 gate on the Patch-14 hook1 word @0x209820.
# It is the PRODUCTION value 0x08131D50 (= j 0x4C7540) -- unchanged from production.
NEW_GATE_MARKER  = P14_HOOK1_JWORD


# ============================================================================
# v148 CAVE RELOCATION MAP  (battle-arena evacuation, mirrors the P27 fix)
# ============================================================================
# A cave-safety audit found that SEVERAL OTHER EXE caves -- not just Patch-27 --
# sat in (or abutting) the EE battle-heap arena (VA >= 0x4B0E00), the same
# false-safe trap that broke battle once before.  v148 evacuates them ALL into
# dead/zero .text padding (VA < 0x4B0DCF), which the game never writes.
#
# THE SAFETY RULE (verified):
#   VA <  0x4B0DCF in dead/zero .text padding  =>  CATEGORICALLY SAFE.
#   VA >= 0x4B0E00 (the arena)                 =>  stompable -- FORBIDDEN.
#   The 0x4AF336 run (202B) abuts the live PsII libgraph descriptor table and is
#   ENTIRELY OFF-LIMITS (it broke the title screen once).
#
# RELOCATION INVARIANCE (the elegant bit): every cave's internal control flow uses
# PC-RELATIVE branches (beq/bne/b: imm = (target-(pc+4))/4).  When the whole cave
# moves by a constant delta, the branch instruction AND its target shift together,
# so the encoded displacement is UNCHANGED.  Absolute `j`/`jal` rejoin targets point
# back into the (unmoved) renderer, and `lui/lbu` table reads point at the (unmoved)
# canonical ADV/LSH tables.  THEREFORE every cave word ships BYTE-IDENTICAL; ONLY the
# cave BASE (where it is written) and its HOOK's `j`-immediate change.  This module is
# the SINGLE SOURCE for those new bases so patch_exe.py can never desync.
#
# NEW BASES (verified-zero dead .text padding; see the audit's fit accounting):
#   P6  trampoline (32B)  0x4B0DD0 -> 0x4B0D4C   (run 0x4B0D4C/52B)
#   P14 cave1 (36B)       0x4C7540 -> 0x4B049C   (run 0x4B049C/36B)
#   P14 cave2 (28B)       0x4C7670 -> 0x4B047C   (tail of run 0x4B0414/132B, after P26)
#   P26 chargen body(104B)0x4C7790 -> 0x4B0414   (run 0x4B0414/132B)
#   P24 narration (24B)   0x4CAA30 -> 0x4AFA58   (run 0x4AFA58/80B, shares w/ P19c2)
#   P19 cave2 (48B)       0x4D6660 -> 0x4AFA70   (same run, after P24)
#   P19 cave1 (68B)       0x4D6600 -> 0x4AB5A8   (run 0x4AB5A8/91B, after P27's 84B)
#
# NOTE: Patch-14's caves were proven never-stomped in-arena, but the audit moves them
# anyway so NOTHING ships in the arena and the guardrail can forbid the arena outright.
# The gate marker @0x209820 therefore CHANGES from the production 0x08131D50 to
# j 0x4B049C; dependent patches 19/24/25/26 gate on RELOC.NEW_GATE_MARKER (updated below).
ARENA_SAFE_HI = 0x4B0DCF      # VA must be < this to be in dead .text padding
LIBGRAPH_LO, LIBGRAPH_HI = 0x4AF2E0, 0x4AF400   # PsII libgraph SDK data -- NEVER touch

# Whitelist of intentional canonical TABLE installs (read-only data the caves index).
# ADV/LSH (0x4C7564/0x4C7690) are resident rodata holes, proven intact across all dumps.
# v173 BATTLE-FIX: the R2100 tables are DROPPED (they softlocked battle at every arena
# placement).  ADV2_VA/LSH2_VA now ALIAS the canonical VAs, so this set is just
# {ADV_VA, LSH_VA} and NOTHING of ours is written into the arena.
CANONICAL_TABLE_VAS = {ADV_VA, LSH_VA, ADV2_VA, LSH2_VA}

# old VA -> new VA for every relocated cave (caves only; tables stay canonical).
# P29 (v155) is NOT a relocation -- it is a NEW cave, split across two verified-zero
# dead .text pads (old_va == new_va); listed here so the safety/overlap self-check +
# tests/test_glyph_metrics_sync.py cover it automatically.
CAVE_RELOC = {
    "P6":    (0x4B0DD0, 0x4B0D4C, 32),    # RenderAllTiles trampoline
    "P14c1": (0x4C7540, 0x4B049C, 36),    # narration advance-LUT cave
    "P14c2": (0x4C7670, 0x4B047C, 28),    # narration draw-shift cave
    "P26":   (0x4C7790, 0x4B0414, 104),   # chargen body-text cave
    "P24":   (0x4CAA30, 0x4AFA58, 24),    # narration boxX=+96 cave
    "P19c2": (0x4D6660, 0x4AFA70, 48),    # chargen draw-shift cave
    "P19c1": (0x4D6600, 0x4AB5A8, 68),    # chargen advance-LUT cave
    "P29f1": (0x4B0C48, 0x4B0C48, 40),    # box-text LSH draw-shift, fragment 1 (10 words)
    "P29f2": (0x4B0BC8, 0x4B0BC8, 24),    # box-text LSH draw-shift, fragment 2 ( 6 words; v175 gender guard)
    # P31 (v157) is a NEW cave (not a relocation): the chargen DESCRIPTION-box LSH
    # draw-shift for renderer 0x307510 (the Patch-26 body-text path).  Split across
    # two verified-zero post-`jr ra` .text pads (old_va == new_va); registered here so
    # the overlap/safety self-check + tests cover it automatically.
    "P31f1": (0x4AFA00, 0x4AFA00, 40),    # 0x307510 desc LSH, fragment 1 (10 words; post-epilogue pad)
    "P31f2": (0x4AB5EC, 0x4AB5EC, 20),    # 0x307510 desc LSH, fragment 2 ( 5 words; tail of P27/P19c1 pad)
}

# Convenience accessors (new VA + new j-hook word) for patch_exe.py.
P6_VA    = CAVE_RELOC["P6"][1]
P14C1_VA = CAVE_RELOC["P14c1"][1]   # OVERRIDE the in-arena value above (v148 relocates it)
P14C2_VA = CAVE_RELOC["P14c2"][1]
P26_VA   = CAVE_RELOC["P26"][1]
P24_VA   = CAVE_RELOC["P24"][1]
P19C1_VA = CAVE_RELOC["P19c1"][1]
P19C2_VA = CAVE_RELOC["P19c2"][1]

# v148: Patch-14 caves moved -> their hook j-words + the gate marker change.
P14_HOOK1_JWORD  = jword(P14C1_VA)   # j 0x4B049C
P14_HOOK2_JWORD  = jword(P14C2_VA)   # j 0x4B047C
NEW_GATE_MARKER  = P14_HOOK1_JWORD   # dependent patches 19/24/25/26 gate on THIS

P6_HOOK_JWORD    = jword(P6_VA)      # j 0x4B0D4C
P26_HOOK_JWORD   = jword(P26_VA)     # j 0x4B0414
P24_HOOK_JWORD   = jword(P24_VA)     # j 0x4AFA58
P19C1_HOOK_JWORD = jword(P19C1_VA)   # j 0x4AB5A8
P19C2_HOOK_JWORD = jword(P19C2_VA)   # j 0x4AFA70


# ============================================================================
# PATCH 29 (v155): BOX-TEXT first-letter-gap fix -- LEFTSHIFT draw-shift for the
# shared chargen/request renderer func 0x3A2EF0.
# ============================================================================
# Patch 27 gave this renderer proportional ADVANCE (pen grows by ADV[gid]) but NOT
# the companion LEFT-BEARING draw-shift (LSH), which the narration renderer already
# has (Patch 14 cave2: subu LEFTSHIFT[gid] @0x4C7690 from the pen before the draw-X
# add).  So box ink lands at baseX + pen + ink_left(gid) and the gap balloons after a
# low-bearing leading capital ("A....llocate").  This patch mirrors Patch 14 cave2 for
# the TWO glyph draw-X sites in 0x3A2EF0:
#   0x3A30F4  addu v1,v0,v1   (path A, mem[sp+0x140]!=0)   ; v1=draw-X, v0=baseX, v1(in)=pen
#   0x3A3170  addu v1,v0,v1   (path B, mem[sp+0x140]==0)
# Both are HOOKED to `jal` ONE shared subroutine.  ra is free inside the 0x3A2EF0 loop
# (saved 0x3A2EF8 sd ra,192(sp); restored ONLY at exit 0x3A31D8 ld ra,192(sp)), so a
# jal-based shared sub is safe.  The jal delay slot at each site is the pristine
# `lbu v0,off(sp)` (0x3A30F8 / 0x3A3174) -- it runs before the sub and CLOBBERS v0
# (=baseX), so the sub RELOADS baseX from sp+0xE0 (matching Patch 27's reload-from-stack
# style).  It returns to site+8 (the dsll32 t0,v1,16 that sign-extends draw-X into t0).
#
# gid recovery: at the draw sites s2 already points PAST the current big-endian u16
# glyph (bumped +2 @0x3A2F6C / 0x3A31C8), so `lbu -1(s2)` = the low byte = gid (char-32,
# <95) -- the SAME recovery Patch 27 uses at these sites.  v158: LSH read from the
# R2100 table LSH2 @0x4B1100 (lui 0x4B + lbu 0x1100 -- this renderer draws the R2100
# upright font in modes 5/7, not R1188; see the v158 R2100 table block above).
#
# MODE GATE on 0x4FED18 in {5,7} (chargen/request) -- battle (mode 8) and the ~250 other
# callers stay byte-identical.  Instead of Patch-27's double-beqz the gate is compacted to
# `(mode-5) & 0xFFFD == 0` (true iff mode in {5,7}: 5->0, 7->2, both clear bit1 -> 0) and
# a `movn t9,zero,at` that ZEROES the shift amount when not gated -> the subu subtracts 0
# -> the STOCK draw-X (baseX+pen) is returned byte-for-byte.  This compaction is REQUIRED:
# no contiguous >=52B safe .text hole remains below the arena, so the sub is SPLIT across
# two verified-zero pads (0x4B0C48/40B and 0x4B0BC8/16B) and the movn form removes the
# second branch that would not have fit.  Behaviour for every non-{5,7} mode is identical
# to the original addu.
#
# v175 GENDER-TILE GUARD: frag1 gained a `sltiu t8,gid,92` + `movz t9,zero,t8` bounds
# guard (gid>=92 -> shift 0 = the tile's natural position); see build_p29().  To make room
# without a 3rd fragment the mode-read TAIL (`lw -0x12E8` + `addiu -5`) moved into frag2,
# which grew 4->6 words (fills its 24B pad exactly).  frag1 stays 10 words.
#
# frag1 @0x4B0C48 (10 words); the internal `j P29_F2_VA` at 0x4B0C68 has its delay slot at
#   0x4B0C6C (still inside the pad), so nothing executes the live data at 0x4B0C70.
# frag2 @0x4B0BC8 (6 words); the `jr ra` at 0x4B0BD8 has its delay slot at 0x4B0BDC (the
#   last word of the 24B pad), so the live EE exception handler at 0x4B0BE0 is never run
#   as a slot.
P29_HOOK1     = 0x3A30F4          # site A  (file 0x2A3174)
P29_HOOK2     = 0x3A3170          # site B  (file 0x2A31F0)
P29_ORIG_SITE = 0x00431821       # addu v1,v0,v1 (pristine at BOTH sites)
P29_F1_VA     = 0x4B0C48          # fragment 1 pad (40B zero; below arena, clear of libgraph)
P29_F2_VA     = 0x4B0BC8          # fragment 2 pad (24B zero; all 6 words used)

def build_p29():
    """Two word lists (frag1, frag2) for the split box-text LSH draw-shift sub.

    v175 GENDER-TILE GUARD: the gender M/F symbols are TILES (glyph id 0x2A0/0x2A1,
    Patch 7); gid recovery `lbu at,-1(s2)` reads their LOW byte = 0xA0/0xA1 = 160/161.
    LSH2 is only TABLE_ENTRIES (92) bytes, and in Option E it is the LAST packed table,
    so an un-guarded LSH2[160] over-read runs 68B off the freed-strncpy-span end into
    live code -> a garbage leftshift (proven 0x2D=45 male / 0xF0=240 female) that FLINGS
    the gender tile off-screen.  The guard `sltiu t8,gid,92` + `movz t9,zero,t8` forces
    the shift to 0 for gid>=92 (the tile's NATURAL position), mirroring the guard Patch
    31 already carries.  gid<92 (all real ASCII text, max 'z'=90) is byte-identical:
    t8=1 -> the movz is a no-op.  t8 is dead at BOTH hook sites (the renderer's own
    `jal 0x3A2E10` at site+~0x30 clobbers it with no prior read -- verified against the
    pristine renderer 0x3A2EF0), so it is a free scratch here.

    To fit the 2 guard words without a 3rd fragment the mode-read TAIL (`lw -0x12E8` +
    `addiu -5`) moved into frag2 (which grows 4->6 words, filling its 24B pad exactly);
    frag1's delay slot keeps `lui at,0x50` so frag2's `lw` has its base.  The mode read
    now spans the frag1->frag2 boundary exactly like Patch 31."""
    frag1 = [
        lw('at', 0xE0, 'sp'),                 # 0x4B0C48  reload baseX (v0 clobbered by jal delay slot)
        addu('v1', 'at', 'v1'),               # 0x4B0C4C  v1 = baseX + pen   (STOCK draw-X)
        lbu('at', -1, 's2'),                  # 0x4B0C50  at = gid (low byte of BE u16; 0..0xFF)
        sltiu('t8', 'at', TABLE_ENTRIES),     # 0x4B0C54  t8 = (gid < 92) ? 1 : 0   [tile/ASCII guard]
        lui('t9', LSH2_VA >> 16),             # 0x4B0C58  LSH2 table base hi (freed strncpy span)
        addu('t9', 't9', 'at'),               # 0x4B0C5C  t9 = LSH2_base + gid
        lbu('t9', LSH2_VA & 0xFFFF, 't9'),    # 0x4B0C60  t9 = LSH2[gid]  (garbage over-read if gid>=92)
        movz('t9', 'zero', 't8'),             # 0x4B0C64  gid>=92 (t8==0) -> t9 = 0  [natural tile pos]
        j(P29_F2_VA),                         # 0x4B0C68  -> frag2 (delay slot below stays in-pad)
        lui('at', 0x50),                      # 0x4B0C6C  (ds) mode read base (absolute, matches Patch 27)
    ]
    frag2 = [
        lw('at', -0x12E8, 'at'),              # 0x4B0BC8  at = mode (RAM 0x4FED18)
        addiu('at', 'at', -5),                # 0x4B0BCC  at = mode - 5
        andi('at', 'at', 0xFFFD),             # 0x4B0BD0  0 iff mode in {5,7}
        movn('t9', 'zero', 'at'),             # 0x4B0BD4  not gated (mode!=5,7) -> t9 = 0
        jr('ra'),                             # 0x4B0BD8  return to site+8
        subu('v1', 'v1', 't9'),               # 0x4B0BDC  (ds) draw-X -= (LSH2 or 0)
    ]
    return frag1, frag2

P29_F1_WORDS, P29_F2_WORDS = build_p29()
P29_HOOK_JWORD = jal(P29_F1_VA)      # jal 0x4B0C48 (installed at BOTH draw sites)


# ============================================================================
# PATCH 31 (v157): CHARGEN DESCRIPTION-box first-letter-gap fix -- LEFTSHIFT
# draw-shift for the chargen body/description renderer func 0x307510.
# ============================================================================
# Patch 26 gave renderer 0x307510 (the LIVE chargen body-text path: line-walk
# 0x307DA0 -> glyph blit 0x307510 -> sprite emit 0x3060B0) a proportional ADVANCE
# (pen s2 grows by ADV[gid], hook @0x3079CC, gated mem[0x4FED18]==5) but NOT the
# companion left-bearing draw-shift (LSH).  So the race/alignment DESCRIPTION boxes
# render UNEVENLY: each glyph's ink lands at penX + glyphX_base + ink_left(gid), so a
# low-bearing leading capital opens a "random space".  This mirrors the Patch-29 fix
# (which gave the OTHER renderer 0x3A2EF0 its LSH companion to Patch 27's ADVANCE).
#
# THE LIVE DRAW-X (statically traced, see the mipsdis of 0x307510):
#   0x307974  lh   t2,0(s2)     ; t2 = penX (the cursor Patch 26 advances)
#   0x307980  addu t2,t2,t0     ; draw-X = penX + glyphX_base   (t0 = lh 8(v1))
#   ...       addu v0,v0,t2 ; sll t1,v0,4  -> the X<<4 passed to emit 0x3060B0.
# All additive, so subtracting LSH from the LOADED penX t2 (at the read, 0x307974)
# subtracts it from the final draw-X WITHOUT touching the stored pen at s2 (Patch 26's
# advance is preserved) -- exactly the Patch-14-cave2 / Patch-29 draw-shift technique.
# There is a SINGLE draw-X site here (unlike 0x3A2EF0's two paths), so ONE hook.
#
# gid recovery: the glyph id being drawn was stored `sd v0,0x10(sp)` @0x307960 (v0 =
# masked 0..0x7FFF; only <0x8000 reaches the draw) 14 insns before the hook and is not
# re-written until after the emit.  So `lhu t8,0x10(sp)` recovers the ACTUAL drawn gid
# in ONE instruction -- the same glyph Patch 26 advanced (on the desc-box text Patch 26
# already renders proportional, so its s7[0] ADV gid == this stored gid; using the
# stored value keeps ADV/LSH in exact lockstep AND is robust on every fetch path).  The
# table read is bounded by `andi 0xFF` (LSH table @0x4C7690 is 256B; tail 95..255 = 0)
# and the real ASCII guard is `sltiu at,gid,95` + movz (gid>=95 -> shift 0), so a
# non-ASCII glyph subtracts nothing.  MODE GATE == 5 ONLY (matching Patch 26 -- 0x307510
# also draws town/menu text at other modes; those keep the stock monospace ADV, so LSH
# must stay 0 there too): `addiu at,mode,-5` + movn t9,zero,at zeroes the shift unless
# mode==5.  Both non-gated cases return the byte-identical stock draw-X (subu t2,t2,0).
#
# The sub is BRANCHLESS (movz/movn) and split across two verified-zero post-`jr ra`
# .text pads below the arena: frag1 @0x4AFA00 (40B, the pad after the 0x4AF9FC epilogue)
# and frag2 @0x4AB5EC (20B, the free tail of the P27/P19c1 post-epilogue run).  Both are
# < 0x4B0DCF and clear of the libgraph block; see build_p31().  v158: reads the R2100
# table LSH2 @0x4B1100 (arena-start hole; the 0x307510 chargen path draws the R2100 upright font).
P31_HOOK      = 0x307974          # lh t2,0(s2) draw-X pen read (file 0x2079F4)
P31_ORIG_SITE = 0x864A0000        # lh t2,0(s2) (pristine at the hook)
P31_F1_VA     = 0x4AFA00          # fragment 1 pad (40B zero; post-epilogue, below arena)
P31_F2_VA     = 0x4AB5EC          # fragment 2 pad (20B zero; tail of P27/P19c1 run)


def build_p31():
    """Two word lists (frag1, frag2) for the split chargen-desc LSH draw-shift sub."""
    frag1 = [
        lh('t2', 0, 's2'),           # 0x4AFA00  reload penX (the displaced hook insn)
        lhu('t8', 0x10, 'sp'),       # 0x4AFA04  gid = stored drawn glyph (0..0x7FFF)
        andi('at', 't8', 0xFF),      # 0x4AFA08  bounded LSH2 table index (0..255) -> safe read
        lui('t9', LSH2_VA >> 16),    # 0x4AFA0C  v174: LSH2 table base (== LSH_VA, segment)
        addu('t9', 't9', 'at'),      # 0x4AFA10  t9 = LSH2_base + (gid & 0xFF)
        lbu('t9', LSH2_VA & 0xFFFF, 't9'),  # 0x4AFA14  t9 = LEFTSHIFT[gid&0xFF] @segment (0 for 95..255)
        sltiu('at', 't8', TABLE_ENTRIES),  # 0x4AFA18  at=(gid<92)?1:0 (guard; table is 92 entries)
        movz('t9', 'zero', 'at'),    # 0x4AFA1C  gid>=95 -> shift = 0
        j(P31_F2_VA),                # 0x4AFA20  -> frag2 (delay slot below stays in-pad)
        lui('at', 0x50),             # 0x4AFA24  (ds) mode read base (absolute, matches Patch 26)
    ]
    frag2 = [
        lw('at', -0x12E8, 'at'),     # 0x4AB5EC  at = mode (RAM 0x4FED18)
        addiu('at', 'at', -5),       # 0x4AB5F0  0 iff mode == 5 (chargen)
        movn('t9', 'zero', 'at'),    # 0x4AB5F4  mode!=5 -> shift = 0 (stock draw-X)
        j(0x30797C),                 # 0x4AB5F8  return to the draw block (past hook+delay)
        subu('t2', 't2', 't9'),      # 0x4AB5FC  (ds) draw-X penX -= (LSH or 0)
    ]
    return frag1, frag2


P31_F1_WORDS, P31_F2_WORDS = build_p31()
P31_HOOK_JWORD = j(P31_F1_VA)        # j 0x4AFA00 (installed at the single draw-X site)


def assert_install_safe(va, size, label, allow_canonical_table=False):
    """GUARDRAIL: raise if a cave/table install lands in (or spills into) the EE
    battle-heap arena (VA >= 0x4B0DCF) or on the PsII libgraph SDK data block.
    This makes future arena placements IMPOSSIBLE.  Canonical read-only tables
    (ADV/LSH @0x4C7564/0x4C7690) are whitelisted (allow_canonical_table=True)."""
    end = va + size
    if allow_canonical_table and va in CANONICAL_TABLE_VAS:
        return  # intentional resident rodata table, not stompable code
    if va >= ARENA_SAFE_HI or end > ARENA_SAFE_HI:
        raise AssertionError(
            "CAVE-SAFETY VIOLATION: %s install VA 0x%06X..0x%06X is in/over the EE "
            "battle-heap arena (>= 0x%06X). Relocate into dead .text padding (VA < 0x%06X)."
            % (label, va, end, ARENA_SAFE_HI, ARENA_SAFE_HI)
        )
    if not (end <= LIBGRAPH_LO or va >= LIBGRAPH_HI):
        raise AssertionError(
            "CAVE-SAFETY VIOLATION: %s install VA 0x%06X..0x%06X overlaps the PsII "
            "libgraph SDK data block (0x%06X..0x%06X) -- the title-hang trap."
            % (label, va, end, LIBGRAPH_LO, LIBGRAPH_HI)
        )


def _selfcheck():
    ok = True
    print("=== piece placement ===")
    # Only the P27 cave is relocated; it must lie in GAP_P27 and BELOW the arena.
    nm, va, ln, gva, glen = ("P27 cave", P27_VA, len(P27_WORDS) * 4, 0x4AB554, 175)
    end = va + ln
    in_gap = (va >= gva and end <= gva + glen)
    below_arena = (end <= ARENA_LO)
    f = "OK" if (in_gap and below_arena) else "FAIL"
    if not (in_gap and below_arena): ok = False
    print("  %-10s VA 0x%06X len %3d end 0x%06X  in-gap=%s below-arena=%s  %s"
          % (nm, va, ln, end, in_gap, below_arena, f))
    # v148: ALL caves relocated below the arena (the audit's battle-arena evacuation).
    print("=== v148 cave relocation map (old -> new), all must be below 0x%06X ===" % ARENA_SAFE_HI)
    spans = []  # (new_lo, new_hi, label) for overlap check
    for label, (old_va, new_va, size) in CAVE_RELOC.items():
        end_new = new_va + size
        safe = (end_new <= ARENA_SAFE_HI) and (end_new <= LIBGRAPH_LO or new_va >= LIBGRAPH_HI)
        if not safe: ok = False
        spans.append((new_va, end_new, label))
        print("  %-6s %3dB  0x%06X -> 0x%06X..0x%06X  safe=%s"
              % (label, size, old_va, new_va, end_new, safe))
    # Overlap check (caves must not collide with each other or with the P27 cave).
    spans.append((P27_VA, P27_VA + len(P27_WORDS) * 4, "P27"))
    spans.sort()
    for i in range(1, len(spans)):
        if spans[i][0] < spans[i - 1][1]:
            print("  FAIL OVERLAP %s vs %s" % (spans[i - 1][2], spans[i][2])); ok = False
    # v175 FIX B: ADV/LSH/ADV2 live in the FREED strncpy span (zero ELF change).
    print("  Option E tables: ADV @0x%06X / LSH @0x%06X / ADV2 @0x%06X / LSH2 @0x%06X "
          "(freed strncpy span; arena PRISTINE)" % (ADV_VA, LSH_VA, ADV2_VA, LSH2_VA))
    _span_lo = STRNCPY_VA + len(build_strncpy_replacement())
    _span_hi = STRNCPY_VA + STRNCPY_ORIG_LEN
    if (_span_lo <= ADV_VA and LSH2_VA + TABLE_ENTRIES <= _span_hi
            and LSH_VA == ADV_VA + TABLE_ENTRIES and ADV2_VA == LSH_VA + TABLE_ENTRIES
            and LSH2_VA == ADV2_VA + TABLE_ENTRIES
            and all((v & 0xFFFF) < 0x8000 for v in (ADV_VA, LSH_VA, ADV2_VA, LSH2_VA))):
        print("  layout OK: 4 tables (ADV/LSH/ADV2/LSH2, 92B each) packed in the freed span "
              "0x%06X..0x%06X; LSH2 = real R2100 leftshift (Option E); low-16 < 0x8000"
              % (_span_lo, _span_hi))
    else:
        print("  FAIL FIX B layout: ADV_VA=0x%06X LSH_VA=0x%06X ADV2_VA=0x%06X "
              "(want inside freed span 0x%06X..0x%06X)"
              % (ADV_VA, LSH_VA, ADV2_VA, _span_lo, _span_hi)); ok = False
    # Gate marker now points at the relocated Patch-14 cave1.
    if NEW_GATE_MARKER != jword(P14C1_VA):
        print("  FAIL gate marker 0x%08X != j 0x%06X" % (NEW_GATE_MARKER, P14C1_VA)); ok = False
    else:
        print("  gate marker @0x209820 == 0x%08X (j relocated P14 cave1 0x%06X)"
              % (NEW_GATE_MARKER, P14C1_VA))
    # Guardrail self-test: every cave install must pass assert_install_safe.
    try:
        for label, (old_va, new_va, size) in CAVE_RELOC.items():
            assert_install_safe(new_va, size, label)
        assert_install_safe(P27_VA, len(P27_WORDS) * 4, "P27")
        print("  guardrail assert_install_safe: all relocated caves PASS")
    except AssertionError as e:
        print("  FAIL guardrail: %s" % e); ok = False
    # v173: the cave reads the CANONICAL ADV table (lui 0x4C + lbu 0x7564).
    has_adv2 = any((w >> 26) == 0x24 and (w & 0xffff) == (ADV2_VA & 0xFFFF) for w in P27_WORDS) \
        and any((w >> 26) == 0x0f and (w & 0xffff) == (ADV2_VA >> 16) for w in P27_WORDS)
    print("  P27 cave reads segment ADV2 @0x%06X (lui 0x%X / lbu 0x%X): %s"
          % (ADV2_VA, ADV2_VA >> 16, ADV2_VA & 0xFFFF, "YES" if has_adv2 else "NO -- FAIL"))
    if not has_adv2: ok = False
    # No relocated piece may touch the PsII libgraph SDK data block (0x4AF2E0..0x4AF400).
    if 0x4AF2E0 <= P27_VA < 0x4AF400 or 0x4AF2E0 <= end - 1 < 0x4AF400:
        print("  FAIL P27 cave overlaps the PsII libgraph block!"); ok = False
    else:
        print("  P27 cave clear of the PsII libgraph block (0x4AF2E0..0x4AF400)")
    # No relocated cave word jumps into the arena.
    print("=== j/branch targets stay out of arena ===")
    for i, wd in enumerate(P27_WORDS):
        op = wd >> 26
        if op == 2 or op == 3:
            tgt = (wd & 0x3ffffff) << 2
            if ARENA_LO <= tgt < ARENA_HI:
                print("  FAIL P27[%d] j 0x%06X -> ARENA" % (i, tgt)); ok = False
    print("  (no FAIL above = clean)")
    return ok


def _disasm(words, base, name):
    Rn = ['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7',
          's0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','s8','ra']
    print("=== %s @0x%06X (%d words) ===" % (name, base, len(words)))
    for i, wd in enumerate(words):
        va = base + i * 4
        op = wd >> 26; rs = (wd >> 21) & 31; rt = (wd >> 16) & 31; rd = (wd >> 11) & 31
        sa = (wd >> 6) & 31; fn = wd & 0x3f; imm = wd & 0xffff
        simm = imm - 0x10000 if imm >= 0x8000 else imm
        if wd == 0: s = "nop"
        elif op == 0:
            if fn == 0x21: s = "addu  %s,%s,%s" % (Rn[rd], Rn[rs], Rn[rt])
            elif fn == 0x23: s = "subu  %s,%s,%s" % (Rn[rd], Rn[rs], Rn[rt])
            elif fn == 0x3c: s = "dsll32 %s,%s,%d" % (Rn[rd], Rn[rt], sa)
            elif fn == 0x3f: s = "dsra32 %s,%s,%d" % (Rn[rd], Rn[rt], sa)
            elif fn == 0x02: s = "srl   %s,%s,%d" % (Rn[rd], Rn[rt], sa)
            else: s = "op0_%02x" % fn
        elif op == 2: s = "j     0x%06X" % ((wd & 0x3ffffff) << 2)
        elif op == 4 and rs == 0 and rt == 0: s = "b     0x%06X" % (va + 4 + simm * 4)
        elif op == 4 and rt == 0: s = "beqz  %s,0x%06X" % (Rn[rs], va + 4 + simm * 4)
        elif op == 4: s = "beq   %s,%s,0x%06X" % (Rn[rs], Rn[rt], va + 4 + simm * 4)
        elif op == 5 and rt == 0: s = "bnez  %s,0x%06X" % (Rn[rs], va + 4 + simm * 4)
        elif op == 0x0f: s = "lui   %s,0x%X" % (Rn[rt], imm)
        elif op == 0x09: s = "addiu %s,%s,%d" % (Rn[rt], Rn[rs], simm)
        elif op == 0x0c: s = "andi  %s,%s,0x%X" % (Rn[rt], Rn[rs], imm)
        elif op == 0x0b: s = "sltiu %s,%s,%d" % (Rn[rt], Rn[rs], simm)
        elif op == 0x23: s = "lw    %s,%d(%s)" % (Rn[rt], simm, Rn[rs])
        elif op == 0x21: s = "lh    %s,%d(%s)" % (Rn[rt], simm, Rn[rs])
        elif op == 0x25: s = "lhu   %s,%d(%s)" % (Rn[rt], simm, Rn[rs])
        elif op == 0x24: s = "lbu   %s,0x%X(%s)" % (Rn[rt], imm, Rn[rs])
        elif op == 0x29: s = "sh    %s,%d(%s)" % (Rn[rt], simm, Rn[rs])
        else: s = "op0x%02X" % op
        print("  0x%06X  %08X  %s" % (va, wd, s))


if __name__ == '__main__':
    import sys
    try:
        sys.stdout.reconfigure(encoding='ascii', errors='replace')
    except Exception:
        pass
    print("v147 RELOCATION DESIGN (v174: tables moved to segment @0x580000)")
    print("P27_VA=0x%06X  (segment ADV @0x%06X / LSH @0x%06X / ADV2 @0x%06X)"
          % (P27_VA, ADV_VA, LSH_VA, ADV2_VA))
    print("hooks: P27 j-word=0x%08X (RELOCATED)  P14h1=0x%08X(GATE,prod)  P14h2=0x%08X(prod)"
          % (P27_HOOK_JWORD, P14_HOOK1_JWORD, P14_HOOK2_JWORD))
    print()
    ok = _selfcheck()
    print()
    _disasm(P27_WORDS, P27_VA, "P27 cave (relocated, canonical table)")
    _disasm(P14C1_WORDS, P14C1_VA, "P14 cave1 advance-LUT (production in-arena)")
    _disasm(P14C2_WORDS, P14C2_VA, "P14 cave2 draw-shift (production in-arena)")
    print("\nSELFCHECK:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)
