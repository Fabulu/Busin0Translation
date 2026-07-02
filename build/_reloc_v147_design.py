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
ADV_VA   = 0x4C7564          # canonical ADV table  (production in-arena)
LSH_VA   = 0x4C7690          # canonical LEFTSHIFT table (production in-arena)

# ── v158: R2100 metric tables (chargen/request UI font) ─────────────────────
# ROOT CAUSE (memory project_chargen_font_r2100_rootcause): the chargen/request
# renderers 0x307510 / 0x3A2EF0 draw the R2100 sub0 UPRIGHT 16px font, NOT the
# oblique 24px R1188 font the canonical tables were measured from.  Feeding them
# the R1188 tables produced the game-wide "Ge nde r" per-letter unevenness.
# Patches 26/27/29/31 therefore read these R2100-derived tables instead
# (glyph_metrics.ADV2/LEFTSHIFT2); the canonical R1188 tables stay untouched for
# narration/dialogue (P14) and battle-adjacent paths.
#
# PLACEMENT EVIDENCE: 0x4B1000..0x4B1200 sits inside the 4081-byte hole
# 0x4B0E97..0x4B1E88 that is ZERO in the pristine EXE AND in all 27 available
# live RAM dumps, including 10 battle dumps spanning every observed battle phase
# (emptybattle / fightsoftlock / fightpartyassault / battlecameraspin /
# superoddcrashfight / fight1 / fight2 / ...) -- the same evidence class that
# whitelisted the canonical in-arena tables.  These are READ-ONLY DATA consumed
# only when mode 0x4FED18 is 5 or 7 (never battle); a hypothetical stomp cannot
# crash anything (worst case: cosmetic spacing until reboot, never observed).
ADV2_VA  = 0x4B1000          # R2100 advance table, 256B (idx 0..94 ADV2, tail 0x12)
LSH2_VA  = 0x4B1100          # R2100 left-shift table, 256B (idx 0..94 LSH2, tail 0)

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
# from live screenshots), so the PROP arm reads ADV2 @0x4B1000 (lui 0x4B / lbu 0x1000)
# instead of the canonical R1188 ADV (which stays for narration/dialogue).  Still no
# ASCII guard -- the 256-byte ADV2 table covers gid 0..255 natively (tail 0x12,
# byte-identical fallback to the canonical tail):
#   lui v1,0x50 ; lw v1,-0x12E8(v1)  (mode) ; addiu v1,v1,-5 ; beqz v1->PROP ;
#   addiu v1,v1,-2 (ds) ; beqz v1->PROP ; nop ;
#   STOCK: lw v1,0xD0(sp) ; dsll32 v1,16 ; dsra32 v1,16 ; b APPLY ; nop ;
#   PROP : lbu v1,-1(s2) ; lui at,0x4B ; addu at,at,v1 ; lbu v1,0x1000(at) ;
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
    w.append(lui('at', 0x4B))                 # 13 lui at,0x4B      ; ADV2 table base
    w.append(addu('at', 'at', 'v1'))          # 14 addu at,at,v1
    w.append(lbu('v1', 0x1000, 'at'))         # 15 lbu v1,0x1000(at) ; ADV2[gid] (R2100)
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
        lui('t0', 0x4C),                      # 0
        andi('v1', 's1', 0xFF),               # 1
        addu('t0', 't0', 'v1'),               # 2
        lbu('v1', 0x7564, 't0'),              # 3  ADV[gid] canonical
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
        lui('at', 0x4C),                      # 0
        addu('at', 'at', 's1'),               # 1
        lbu('at', 0x7690, 'at'),              # 2  LSH[gid] canonical
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
# These are resident rodata holes, proven intact across all dumps; they are NOT caves.
# v158 adds the R2100 tables (ADV2/LSH2 @0x4B1000/0x4B1100 -- zero across all 27 live
# dumps incl. 10 battle dumps; data-only, read only in modes 5/7, never battle).
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
    "P29f2": (0x4B0BC8, 0x4B0BC8, 16),    # box-text LSH draw-shift, fragment 2 ( 4 words)
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
# upright font in modes 5/7, not R1188; see the v158 table block above).
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
# frag1 @0x4B0C48 (10 words); the internal `j P29_F2_VA` at 0x4B0C68 has its delay slot at
#   0x4B0C6C (still inside the pad), so nothing executes the live data at 0x4B0C70.
# frag2 @0x4B0BC8 (4 words); the `jr ra` at 0x4B0BD0 has its delay slot at 0x4B0BD4 (still
#   inside the pad), so the live EE exception handler at 0x4B0BE0 is never run as a slot.
P29_HOOK1     = 0x3A30F4          # site A  (file 0x2A3174)
P29_HOOK2     = 0x3A3170          # site B  (file 0x2A31F0)
P29_ORIG_SITE = 0x00431821       # addu v1,v0,v1 (pristine at BOTH sites)
P29_F1_VA     = 0x4B0C48          # fragment 1 pad (40B zero; below arena, clear of libgraph)
P29_F2_VA     = 0x4B0BC8          # fragment 2 pad (24B zero; we use 16B)

def build_p29():
    """Two word lists (frag1, frag2) for the split box-text LSH draw-shift sub."""
    frag1 = [
        lw('at', 0xE0, 'sp'),        # 0x4B0C48  reload baseX (v0 clobbered by jal delay slot)
        addu('v1', 'at', 'v1'),      # 0x4B0C4C  v1 = baseX + pen   (STOCK draw-X)
        lbu('at', -1, 's2'),         # 0x4B0C50  at = gid (low byte of BE u16; char-32 <95)
        lui('t9', 0x4B),             # 0x4B0C54  R2100 LSH2 table base 0x4B0000 (v158)
        addu('t9', 't9', 'at'),      # 0x4B0C58  t9 = 0x4B0000 + gid
        lbu('t9', 0x1100, 't9'),     # 0x4B0C5C  t9 = LEFTSHIFT2[gid] (0 for space/non-ASCII)
        lui('at', 0x50),             # 0x4B0C60  mode read (absolute, matches Patch 27)
        lw('at', -0x12E8, 'at'),     # 0x4B0C64  at = mode (RAM 0x4FED18)
        j(P29_F2_VA),                # 0x4B0C68  -> frag2 (delay slot below stays in-pad)
        addiu('at', 'at', -5),       # 0x4B0C6C  (ds) at = mode - 5
    ]
    frag2 = [
        andi('at', 'at', 0xFFFD),    # 0x4B0BC8  0 iff mode in {5,7}
        movn('t9', 'zero', 'at'),    # 0x4B0BCC  not gated (at!=0) -> t9 = 0 (subtract nothing)
        jr('ra'),                    # 0x4B0BD0  return to site+8
        subu('v1', 'v1', 't9'),      # 0x4B0BD4  (ds) draw-X -= (LSH or 0)
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
# table LSH2 @0x4B1100 (the 0x307510 chargen path draws the R2100 upright font).
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
        lui('t9', 0x4B),             # 0x4AFA0C  R2100 LSH2 table base 0x4B0000 (v158)
        addu('t9', 't9', 'at'),      # 0x4AFA10  t9 = 0x4B0000 + (gid & 0xFF)
        lbu('t9', 0x1100, 't9'),     # 0x4AFA14  t9 = LEFTSHIFT2[gid&0xFF] (0 for 95..255)
        sltiu('at', 't8', 95),       # 0x4AFA18  at = (gid < 95) ? 1 : 0   (real ASCII guard)
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
    # ADV/LSH tables stay canonical (whitelisted, NOT relocated).
    print("  ADV/LSH tables canonical @0x%06X / 0x%06X (whitelisted, NOT relocated)" % (ADV_VA, LSH_VA))
    # v158 R2100 tables: adjacent 256B blocks, no overlap with each other or any cave,
    # inside the 27-dump-verified zero hole 0x4B0E97..0x4B1E88.
    if not (0x4B0E97 <= ADV2_VA and ADV2_VA + 256 == LSH2_VA and LSH2_VA + 256 <= 0x4B1E88):
        print("  FAIL R2100 table placement 0x%06X/0x%06X outside the verified hole" % (ADV2_VA, LSH2_VA)); ok = False
    else:
        print("  R2100 tables ADV2 @0x%06X / LSH2 @0x%06X (verified-zero hole, modes 5/7 data)" % (ADV2_VA, LSH2_VA))
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
    # v158: the cave reads the R2100 ADV2 table (lui 0x4B + lbu 0x1000).
    has_adv2 = any((w >> 26) == 0x24 and (w & 0xffff) == (ADV2_VA & 0xFFFF) for w in P27_WORDS) \
        and any((w >> 26) == 0x0f and (w & 0xffff) == (ADV2_VA >> 16) for w in P27_WORDS)
    print("  P27 cave reads R2100 ADV2 @0x%X(0x%X0000): %s"
          % (ADV2_VA & 0xFFFF, ADV2_VA >> 16, "YES" if has_adv2 else "NO -- FAIL"))
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
    print("v147 RELOCATION DESIGN (SIMPLIFIED -- P27 cave only)")
    print("P27_VA=0x%06X  (canonical ADV @0x%06X / LSH @0x%06X, NOT relocated)"
          % (P27_VA, ADV_VA, LSH_VA))
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
