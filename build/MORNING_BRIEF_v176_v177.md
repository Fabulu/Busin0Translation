# Morning brief — v176 (gender) + v177 (banner)

Two ISOs are built and gated. **v176 is a solid GO. v177 needs your boot-test to close out** — the banner fix couldn't be finished blind (see below), so I shipped the safe, testable version and left you a decision tree.

---

## v176 — gender fix — **GO, verified, publishable**
`build/BUSIN0_EN_v176_gender.iso` — md5 `f3db1f1b711baaa090ae8db27e748b2b`

- **Fixes:** the flung/off-screen gender M/F symbols.
- **Cause:** the box-text leftshift cave P29 was unguarded; the gender tile id (0x2A0 → low byte 160) over-read the 92-entry leftshift table. In FIX B the over-read landed in a neighbor table (small value → OK); Option E moved LSH2 to the span end, so it ran into live code (0x2D=45px / 0xF0=240px = the fling). Added the `sltiu<92`+`movz` guard P31 already had → id≥92 uses shift 0 (natural tile position).
- **Verified:** guard present in the built cave; gender ids 160/161 → shift 0; **text tables byte-identical, strncpy + all arena zero-windows untouched (battle fix intact); 328/0.**
- **Boot check:** both ♂ and ♀ sit in the gender box, ♂ ringed when selected. Chargen text still clean. Harpy still dies.

---

## v177 — banner restore — **BOOT-TEST REQUIRED before publish**
`build/BUSIN0_EN_v177_banner.iso` — md5 `68c70a600e671331b2b912c6f6a7415c`
= v176 **+ Patch 6 disabled** (JAL site reverted to stock `0x0C0C2E10`; RenderAllTiles now runs in chargen). Only delta from v176 is Patch 6. Gender guard, text, battle all identical to v176.

### What Patch 6 actually does (corrected)
RenderAllTiles draws BOTH the chargen **kanji overlay** and every scene/dialogue **portrait**. Patch 6 is a *mode-gated* trampoline: skip RenderAllTiles **only in chargen (mode 5)** → hides the kanji there, portraits alive everywhere else. (The *original* Patch 6 NOP'd it globally and killed all portraits; the mode-gate fixed that.) So it's doing a real job — hiding a Japanese overlay on chargen. The banner is collateral: it's also a RenderAllTiles tile, so the blanket mode-5 skip throws it out too.

**Disabling Patch 6 (what v177 does) reverts the call to stock → RenderAllTiles runs normally → portraits render exactly as pristine.** No portrait risk (the kill was the old *global* NOP, not this). The banner comes back. The *only* thing in question is whether the chargen kanji overlay is still Japanese or now English (our later R2100/R2138 work may have already translated it — lean: probably English, but unproven, because the tile list is freed each frame and unreadable statically).

A *selective* filter (keep banner, skip only the kanji tile-id) is the ideal end-state, but its discriminator is the **tile id**, and all 10 chargen saves read a null list — so the ids need a **live capture**. v177 is the diagnostic that both restores the banner AND lets you read those ids.

### Boot v177 and check TWO things
1. **Is the white section-banner back** at the bottom of chargen (and does it re-cover the giant "Personality")? → should be **yes**.
2. **Does any untranslated JP kanji re-appear** on the chargen screens? → the whole question. (Lean: no, since the atlases were translated — but this is the thing to confirm.)
*(Portraits are NOT at risk — disabling Patch 6 = stock RenderAllTiles = portraits render as normal. No need to check.)*

### Decision tree
- **Banner back + no kanji + portraits fine → v177 is the complete fix. Publish v177** (I'll make Patch-6-off the default + cut the release).
- **Kanji re-appears (or portraits regress) → don't publish v177.** We need the selective Patch 6, and I have everything to build it *except* the tile ids. Grab them in one PCSX2 session (procedure below) and I'll finish it same-day.

### Capture procedure (only if v177 re-shows kanji)
On the chargen Gender/Personality frame, in PCSX2:
- EE exec breakpoint at **VA 0x2F2568** (the RenderAllTiles call site) — or loop entry 0x30B840.
- When it hits, dump the tile array: base ptr = `*(0x4FE70C)`, then **32 records × 50 bytes**.
- Report per record: **+0x00 (tile id)**, +0x12 (width), +0x24 (flags), +0x2F (enable). The wide, low-Y record is the banner; the narrow one(s) are the kanji.
- With those ids I build the in-loop id-filter cave (keep banner, `j 0x30BBA0` to skip the kanji id) — small, gated, battle-safe.

### RenderAllTiles reference (for the selective fix)
32-slot loop @0x30B840 over 50-byte records at `*(gp-0x68E4)=0x4FE70C`; id at +0x00 indexes a 679-entry descriptor table at `*(gp-0x68E8)=0x4FE708`. Existing per-tile skip gates (all branch to loop-continue 0x30BBA0): id==0xFFFF, id≥679, descriptor.word0==0, flags+0x24 & 0x8000, enable+0x2F==0. Hook point for the filter: just after the id load/range-check (~0x30B884, id in a0), cave in verified-zero .text below 0x4B0DCF.

---

## Publish note
I have **not** published anything (standing rule + your "test first"). When you've picked the winner, say the word and I'll run the release train (pyxdelta encode+roundtrip → site index/app.js/README → npm deploy → live md5 verify). v176 is publishable as-is if you'd rather ship the gender fix now and settle the banner separately.
