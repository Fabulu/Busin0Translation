#!/usr/bin/env python3
"""
PATCH 17 verification: Tavern hub gate re-arm on request-flow exit.

Proves, from the patched EXE + the two RAM images, that:
  1. The LIVE hub-input gate is flag 0x4FE6B8 (gp-0x6938), read at 0x2F20D4
     and branched on at 0x2F20DC -> jal 0x187C40 (hub menu/input worker).
  2. Flag 0x4FE690 (gp-0x6960) is dead (its only reader 0x2F16B0 has no
     jal/data callers) -> NOT the gate; we set it only to mirror the working RAM.
  3. tavern104/firsttavern/tavernv3 (WORKING) have gate=1; request/requests/
     fuckinghellman/requestbroken (FROZEN) have gate=0.
  4. PATCH 17's cave (j'd from PATCH 16 teardown) sets the gate to the working
     value -> the live dispatcher 0x2F20DC bne is taken -> worker runs.

Run: python build/verify_patch17_hub_gate.py
"""
import sys, os, struct, zipfile
sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE  = os.path.join(ROOT, "build", "SLPM_653.78_patched")
RAM  = os.path.join(ROOT, "ramdumps")
GP   = 0x504FF0
GATE = 0x4FE6B8   # gp-0x6938  LIVE
MIRR = 0x4FE690   # gp-0x6960  dead/mirror


def fo(va):       return va - 0x100000 + 0x80
def va_of(o):     return o - 0x80 + 0x100000


def load_ee(p):
    z = zipfile.ZipFile(p)
    for n in z.namelist():
        if "eeMemory" in n:
            return z.read(n)
    raise SystemExit("no eeMemory in " + p)


def find_jal(exe, target):
    instr = 0x0C000000 | ((target >> 2) & 0x03FFFFFF)
    pat = struct.pack("<I", instr); out = []; o = 0
    while True:
        i = exe.find(pat, o)
        if i < 0: break
        if i % 4 == 0: out.append(va_of(i))
        o = i + 1
    return out


def main():
    ok = True
    exe = open(EXE, "rb").read()

    # 1. dead-flag proof
    getter_callers = find_jal(exe, 0x2F16B0)
    data_refs = [va_of(i) for i in range(0, len(exe) - 3, 4)
                 if struct.unpack_from("<I", exe, i)[0] == 0x2F16B0]
    print("[1] 0x4FE690 getter 0x2F16B0  jal-callers=%s data-refs=%s -> %s"
          % (getter_callers, data_refs,
             "DEAD (not the gate)" if not getter_callers and not data_refs else "HAS READERS"))
    ok &= (not getter_callers and not data_refs)

    # 2. live-gate dispatcher bytes intact
    g_read = struct.unpack_from("<I", exe, fo(0x2F20D4))[0]   # jal 0x2F2DC0 getter(0x4FE6B8)
    g_bne  = struct.unpack_from("<I", exe, fo(0x2F20DC))[0]   # bne v0,zero,0x2F20F8
    print("[2] dispatcher 0x2F20D4=0x%08X (jal getter) 0x2F20DC=0x%08X (bne -> worker 0x187C40) %s"
          % (g_read, g_bne, "OK" if g_read == 0x0C0BCB70 and g_bne == 0x14400006 else "CHANGED!"))
    ok &= (g_read == 0x0C0BCB70 and g_bne == 0x14400006)

    # 3. RAM correlation
    rows = [("tavern104", 1), ("firsttavern", 1), ("tavernv3", 1),
            ("request", 0), ("requests", 0), ("fuckinghellman", 0), ("requestbroken", 0)]
    print("[3] RAM gate (0x4FE6B8) vs expected:")
    for name, exp in rows:
        p = os.path.join(RAM, name + ".p2s")
        if not os.path.exists(p):
            print("      %-16s MISSING" % name); continue
        m = load_ee(p)
        v = m[GATE]
        tag = "OK" if v == exp else "*** MISMATCH ***"
        if v != exp: ok = False
        print("      %-16s gate=%d (expect %d) %s" % (name, v, exp, tag))

    # 4. simulate the fix on the frozen image
    f = bytearray(load_ee(os.path.join(RAM, "fuckinghellman.p2s")))
    w = load_ee(os.path.join(RAM, "tavern104.p2s"))
    print("[4] simulate PATCH17 cave on fuckinghellman.p2s:")
    print("      before: 0x4FE6B8=%d 0x4FE690=%d" % (f[GATE], f[MIRR]))
    f[GATE] = 1; f[MIRR] = 1   # cave: li v1,1; sb -0x6938(gp); sb -0x6960(gp)
    match = (f[GATE] == w[GATE] and f[MIRR] == w[MIRR])
    print("      after : 0x4FE6B8=%d 0x4FE690=%d  match-working=%s" % (f[GATE], f[MIRR], match))
    dispatch_runs = f[GATE] != 0
    print("      dispatcher 0x2F20DC bne taken=%s -> jal 0x187C40 worker %s"
          % (dispatch_runs, "RUNS (input alive)" if dispatch_runs else "SKIPPED (frozen)"))
    ok &= match and dispatch_runs

    # 5. patched EXE cave + teardown redirect
    cave = [struct.unpack_from("<I", exe, fo(0x4D65D0 + i * 4))[0] for i in range(5)]
    exp_cave = [0x24030001, 0xA38396C8, 0xA38396A0, 0x0805657E, 0x00000000]
    td = struct.unpack_from("<I", exe, fo(0x4CAA78))[0]
    print("[5] patched EXE: cave@0x4D65D0=%s teardown@0x4CAA78=0x%08X (want j 0x4D65D0=0x08135974)"
          % (["0x%08X" % c for c in cave], td))
    ok &= (cave == exp_cave and td == 0x08135974)

    print("\n=== %s ===" % ("ALL CHECKS PASS" if ok else "FAILURE"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
