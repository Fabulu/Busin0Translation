content = r"""# Recon 4 (R3) - Tavern request-list text path + size-branch + Patch 22/25 audit

Date 2026-06-23. EXE: pristine extracted/SLPM_653.78 (disasm); patched probe via live
ramdumps/requestperfect.p2s (newest, 22:16, this round capture). file_off = VA - 0x100000 + 0x80.
EE RAM in eeMemory.bin: VA == file offset. Extracted to build/harvest/_requestperfect/.

## 0. TL;DR (high confidence)
- Request DESCRIPTION BODY renders through func 0x307DA0 Block-2 (align==2, pen sp+0x1ce) -- SAME
  universal dispatcher as narration/dialogue, NOT func 0x307510 (chargen) and NOT dead
  jal 0x305E30/0x308030. PROVEN: Patch 22 advance edit at 0x308CB0 (24->18) IS LANDING -- measured
  live body pitch ~20px (pristine ~26px). Patch 22 on CORRECT path (unlike inert Patch 19). "Same
  wide spacing as chargen" = coincidence of both ~18px mono now, not a shared renderer.
- Request body size-branch = INTEGER MONOSPACE (DEFAULT, metric flag sp+0x110==100). Resolved by
  measurement: line-3 pitch constant ~19-21px regardless of glyph -> monospace. COP2/float branch
  (0x308CC0, flag!=100) NOT taken.
- Client/Reward/Deadline labeled rows = DIFFERENT path: draw_clamp12 @0x3A3300 (recon W3). They do
  NOT hit 0x308CB0; Patch 22/25 do nothing to them.
- Patch 22 (patch_exe.py:972) = CORRECT and LIVE (all 4 sites present). Not dead.
- Patch 25 (patch_exe.py:1088) = correctly authored, ships DISABLED (PATCH25_ENABLE=False). Hooks
  0x308CAC -> cave 0x4CAA48 adding proportional ADV-table advance (mirror Patch 14). All encodings,
  gid extraction (cell>>8 HIGH byte = correct for Block-2), table lookup, jump targets VERIFY; cave
  0x4CAA48..0x4CAA6F zero-pad, no overlap with Patch-24 cave. Ready to enable after ONE live check.
- Blurriness = GS-side magnification of 16x16 PSMT4 tiles (TEX1 MMAG). Not a trivial isolated EXE
  lever. LEAVE IT unless live GS reg trace shows MMAG=1.

## 1. Provenance -- requestperfect.p2s matches shipped v133-class patched EXE (NOT stale)
0x308CB0=0x24420012 (P22 adv +18); 0x308D7C=0x24420012 (P22 adv sibling); 0x30896C=0x000410C0
(P22 reserve head); 0x308974=0x00021040 (P22 reserve tail); 0x308328=0x24040008 (P23 li a0,8);
0x30973C=0x08132A8C (P24 boxX cave); 0x308CAC=0x87A201CE (P25 hook PRISTINE -> P25 NOT installed);
0x3097A0=0x08131D50 (P14 marker); 0x308040=0x08135980 (P19/diag hook); 0x3079DC=0x24420012
(0x307510 int mono stride edited); 0x3076FC=0x344251EC (0x307510 float pitch edited);
screen-mode 0x4FED18=0x00000007 (REQUEST screen).

## 2. Request body IS func 0x307DA0 Block-2 (align==2) -- EXE + measured
Dispatch: 0x308928 li v0,2 / 0x30892C bne v1,v0 (align==2 fall-through to Block-2).
Advance branch (pristine; P22 edits +24s to +18):
  0x308C84 jal 0x3060B0 (draw)
  0x308CA0 lw v0,0x110(sp)      ; sp+0x110 = font metric/SIZE flag
  0x308CA4 bne v0,100,0x308CC0  ; flag!=100 -> COP2 FLOAT proportional
  0x308CAC lh v0,0x1ce(sp)      ; ==100 DEFAULT (mono) pen   <-- Patch 25 hook
  0x308CB0 addiu v0,v0,0x18     ; +24 pristine / +18 P22  (MONO stride)
  0x308CB4 beq ...,0x308CD8 ; 0x308CB8 sh v0,0x1ce(sp)
  0x308CC0.. COP2 path: lh pen / cvt.w.s / addu / sh
  0x308CD8 addiu s5,s5,2 ; lh v1,2(s5) ; bne v1,-1 -> loop (0xFFFF term)
Sibling: 0x308D7C addiu v0,v0,0x18 (v1==7 branch, also +18 live).
PROOF: live body line-3 pitch ~19-21px CONSTANT (build/harvest/_measure_rp.py); pristine ~26px =>
+18 edit reaches glyphs => body genuinely on 0x308CB0. Not inert.

## 3. Size-branch (PRIMARY unknown) -- REQUEST body = INTEGER (==100)
Block-2 selector sp+0x110 set @0x308AA0 (sw v0) from COP1 of float @0x308A80 (lh v0,0x190(sp)); next
insns load 0x3E75C28F @0x308AAC/0x308AB4 (proportional pitch const family, mirrors chargen
0x3E7551EC) => sp+0x110 IS font SIZE, same ==100-mono / !=100-float structure as 0x307510 but a
DIFFERENT function/frame. Branch taken for English body = ==100 INTEGER MONOSPACE (constant ~20px
pitch). The float descriptor source is UNCONFIRMED statically but NOT needed -- measurement decisive.
Same reason user sees identical wide spacing on chargen and request: two distinct mono sites both at
~18px after round-1 edits.

## 4. Patch 22 / Patch 25 audit
### Patch 22 (patch_exe.py:935-991) -- CORRECT, LIVE, right path
Sites: 0x2089EC->0x000410C0 (reserve head 0x30896C); 0x2089F4->0x00021040 (reserve tail 0x308974);
0x208D30->0x24420012 (adv 0x308CB0); 0x208DFC->0x24420012 (adv sibling 0x308D7C). All confirmed
live. Took body 24px->18px mono. box_base=lh 0x1ce(sp) @0x30894C (per-line pen reset);
origin = box_base + (box_width - count)*pitch (center-anchored).

### Patch 25 (patch_exe.py:1088-1206) -- correctly authored, DISABLED, ready
hook 0x308CAC pristine 0x87A201CE -> j 0x4CAA48 (0x08132A92 OK); delay 0x308CB0 -> nop;
cave 0x4CAA48: lhu v0,2(s5); srl t8,v0,8 (gid HIGH byte, CORRECT for (char-32)<<8); lui at,0x4C;
addu at,at,t8; lbu t9,0x7564(at); lh v0,0x1ce(sp); addu v0,v0,t9; sh v0,0x1ce(sp); j 0x308CD8
(0x080C2336 OK); nop. margin 0x308968 subu a0,v0,a0 -> move a0,zero (0x00002021 OK) => reserve=0,
origin=box_base (Option-B fixed-left). Cave 0x4CAA48..0x4CAA6F ZERO in pristine; P24 cave ends
0x4CAA47 -> NO overlap. ADV table @0x4C7564 RESIDENT/live (space=9,M=23,i=12,D=23,u=17). P14 marker
0x3097A0=0x08131D50 present. gid asymmetry vs P14 cave (andi 0xFF low byte) intentionally correct.
Verdict: P25 hooks the exact DEFAULT advance the body uses; not a wrong/dead site; gated OFF pending
sec-5 live check.

## 5. The ONE live BP needed before enabling Patch 25
Option-B (margin a0=0 -> origin=box_base) is correct only if box_base (v1=lh 0x1ce(sp) @0x30894C) is
the parchment LEFT edge, not center. box_base = running pen at line start. BREAK 0x308980 (or read
sp+0x1ce after 0x308988) on a known line; compare stored origin to measured parchment left-x (~x=120
in 640-wide shot). If left edge: enable P25 as-is (Option B). If center: Option B WRONG -> Option A
(sum(ADV[gid]) re-center, B4 sketched it). Also confirm hook fires + body stays ==100 (bp 0x4CAA48).

## 6. Does proportional alone fix it?
Narrows body only ~17-19% vs current 18px mono (avg ADV 17.4 vs 18). Right lever for the wide-mono
complaint, but nothing for Client/Reward/Deadline (clamp12, W3); and with center reserve still
count*18 a proportional advance mis-centers ~count*1.6px left (B4 sec2) -- P25 Option-B margin=0
sidesteps via fixed-left, valid only if box_base==left (sec 5). RECOMMEND: enable P25 after sec-5
confirm; treat labeled rows separately.

## 7. Blurriness
16x16 PSMT4 CLUT sprites from 0x3000 atlas via 0x3060B0. Blur = GS magnification (TEX1 MMAG=LINEAR)
when tile drawn into >16px cell, or sub-pixel placement. Levers: (a) integer placement (proportional
advance nudges to integer px, minor help); (b) force TEX1 MMAG=0 (NEAREST) in 0x3060B0 -- GS-side,
SHARED by ALL glyph text => global, sharpens everything. Not isolated. LEAVE IT unless live GS trace
confirms MMAG=1 on body draw. Low priority.

## 8. Files / offsets
patch_exe.py: P22 @L935 (sites L973-979), P23 @L993, P24 @L1039, P25 @L1088 (ENABLE flag L1142,
cave L1154-1165). func 0x307DA0 Block-2: dispatch @0x308928/0x30892C; box_base=lh 0x1ce(sp)
@0x30894C; reserve subu @0x308968 (P25 margin) / *pitch 0x30896C-0x308974 (P22) / origin @0x308980 /
store @0x308988; size flag @0x308AA0 (COP1 of 0x190(sp)); adv DEFAULT @0x308CAC/0x308CB0, COP2
@0x308CC0, sibling @0x308D7C. ADV table @0x4C7564; P14 cave @0x4C7540; marker @0x3097A0;
box_width=sp+0x140 @0x30839C. Live cells: bring @0xE3734F, Duhan @0xE37607.
Probes: build/harvest/_rp_probe.py, _measure_rp.py, _findbody.py, _advtable.py, _disasm.py.

## 9. NEEDS LIVE DEBUGGER
1. box_base @0x308980 == box LEFT vs CENTER -> decides P25 Option-B vs Option-A. THE gate before
   PATCH25_ENABLE=True.
2. Confirm P25 hook fires per glyph + body stays ==100 with cave installed (bp 0x4CAA48).
3. (Optional) GS TEX1 MMAG on body draw -> blur lever decision.

## 10. UNCONFIRMED
- Exact font-descriptor float making sp+0x110==100 (chased to 0x308A80 lh 0x190(sp)->COP1, not a
  single constant). NOT needed.
- W3 clamp12 attribution for Client/Reward/Deadline taken as given (re-confirmed only that those rows
  are NOT on 0x308CB0).
"""
p = r"C:\programmieren\wizardrytranslation\runs\CLAUDE-RUNS\RUN-20260623-1835-box-request-formatting\subagents\recon4-R3-request-path\FINDINGS.md"
open(p, "w", encoding="utf-8").write(content)
print("written", len(content), "bytes ->", p)
