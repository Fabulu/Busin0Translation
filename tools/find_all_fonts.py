import json, struct, os, sys, re

RESDIR = "C:/Programmieren/wizardrytranslation/extracted/packdata_resources"
EXEPATH = "C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78"
OUTDIR = "C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260522-1932-initial-recon/subagents/impl09-all-fonts"

def hexdump(data, offset=0, length=None):
    if length: data = data[:length]
    lines = []
    for i in range(0, len(data), 16):
        c = data[i:i+16]
        h = " ".join(f"{b:02x}" for b in c)
        a = "".join(chr(b) if 32<=b<127 else "." for b in c)
        lines.append(f"  {offset+i:08x}: {h:<48s} {a}")
    return "\n".join(lines)

def parse_tex0(header):
    if len(header) < 0x58: return {}
    t = struct.unpack_from("<Q", header, 0x50)[0]
    psm = (t>>20)&0x3F; tw=(t>>26)&0xF; th=(t>>30)&0xF
    pn = {0:"PSMCT32",1:"PSMCT24",2:"PSMCT16",19:"PSMT8",20:"PSMT4",27:"PSMT8H"}
    return {"tbp0":t&0x3FFF,"tbw":(t>>14)&0x3F,"psm":psm,"psm_name":pn.get(psm,f"PSM{psm}"),
            "tw":tw,"th":th,"w":1<<tw,"h":1<<th,"tcc":(t>>34)&1,"cbp":(t>>37)&0x3FFF,
            "cpsm":(t>>51)&0xF,"cld":(t>>61)&7}

def is_gs_header(header):
    if len(header) < 0x1C: return False
    return (struct.unpack_from("<I",header,0x14)[0]==0x10000000 and
            struct.unpack_from("<I",header,0x18)[0]==0x0e)

def main():
    out = []
    def log(m=""): print(m); out.append(m)
    NUL = bytes([0])
    M80 = bytes([0x80]*4)
    wk = "w"
    hk = "h"

    with open(os.path.join(RESDIR,"manifest.json")) as f:
        manifest = json.load(f)
    log(f"Scanned {len(manifest)} PACKDATA resources")

    log("\n"+"="*70); log("PHASE 1: Reference resource 1272"); log("="*70)
    with open(os.path.join(RESDIR,"1272_type01.bin"),"rb") as f: ref=f.read()
    log(f"Size: {len(ref)} bytes"); log("Header:"); log(hexdump(ref[:192]))
    ri = parse_tex0(ref)
    log(f"TEX0: {ri[wk]}x{ri[hk]} {ri['psm_name']} TBP0={ri['tbp0']} TBW={ri['tbw']}")
    clut = ref[-64:]
    log("Palette (last 64B = 16 RGBA):")
    for i in range(16):
        rv,gv,bv,av = clut[i*4],clut[i*4+1],clut[i*4+2],clut[i*4+3]
        log(f"  Color {i:2d}: R={rv:3d} G={gv:3d} B={bv:3d} A={av:3d}")

    log("\n"+"="*70); log("PHASE 2: PSMT4 > 30KB"); log("="*70)
    psmt4_big = []
    for entry in manifest:
        if entry.get("skipped"): continue
        fp = os.path.join(RESDIR, entry["filename"])
        if not os.path.exists(fp): continue
        fs = os.path.getsize(fp)
        if fs < 30000: continue
        with open(fp,"rb") as f: hd=f.read(192)
        if not is_gs_header(hd): continue
        ti = parse_tex0(hd)
        if ti.get("psm") == 20:
            psmt4_big.append((entry["index"],fs,ti,entry["filename"]))
    log(f"Found {len(psmt4_big)}:")
    for idx,fs,ti,fn in psmt4_big:
        mk = " <<< CONFIRMED" if idx==1272 else ""
        log(f"  Res {idx:4d}: {fs:8d}B {ti[wk]}x{ti[hk]} TBP0={ti['tbp0']} TBW={ti['tbw']}{mk}")

    log("\n"+"="*70); log("PHASE 3: Resources 1265-1285"); log("="*70)
    for entry in manifest:
        if entry.get("skipped"): continue
        idx = entry["index"]
        if not (1265<=idx<=1285): continue
        fp = os.path.join(RESDIR, entry["filename"])
        if not os.path.exists(fp): continue
        fs = os.path.getsize(fp)
        with open(fp,"rb") as f: d=f.read(192)
        ti = parse_tex0(d) if is_gs_header(d) else {}
        ps = f" -> {ti[wk]}x{ti[hk]} {ti['psm_name']}" if ti else ""
        log(f"  Res {idx}: {fs:8d}B tc={entry['type_code']}{ps}")

    log("\n"+"="*70); log("PHASE 4: PSMT4 with grayscale CLUT"); log("="*70)
    gray_fonts = []
    for entry in manifest:
        if entry.get("skipped"): continue
        fp = os.path.join(RESDIR, entry["filename"])
        if not os.path.exists(fp): continue
        fs = os.path.getsize(fp)
        if fs < 256: continue
        with open(fp,"rb") as f: hd=f.read(192); f.seek(max(0,fs-64)); cl=f.read(64)
        if not is_gs_header(hd): continue
        ti = parse_tex0(hd)
        if ti.get("psm") != 20 or len(cl)<64: continue
        is_gray = all(cl[i*4]==cl[i*4+1]==cl[i*4+2] for i in range(16))
        if is_gray:
            vals = [cl[i*4] for i in range(16)]
            gray_fonts.append((entry["index"],fs,ti,entry["filename"],vals))
    log(f"Found {len(gray_fonts)} PSMT4 with grayscale CLUT:")
    for idx,fs,ti,fn,vals in gray_fonts:
        log(f"  Res {idx:4d}: {fs:8d}B {ti[wk]}x{ti[hk]} CLUT[0..3]={vals[:4]}")

    log("\n"+"="*70); log("PHASE 5: FCD_ names in EXE"); log("="*70)
    with open(EXEPATH,"rb") as f: exe=f.read()
    for m in re.finditer(rb"FCD_[a-z_]+", exe):
        o = m.start()
        try: ei=exe.index(NUL,o,o+64)
        except ValueError: ei=o+64
        s = exe[o:ei].decode("ascii",errors="replace")
        log(f"  0x{o:08x}: {s}")

    log("\n"+"="*70); log("PHASE 6: Font descriptors at 0x3C0700"); log("="*70)
    dd = exe[0x3C0700:0x3C0860]
    p80 = [i for i in range(len(dd)-4) if dd[i:i+4]==M80]
    log(f"0x80808080 at: {p80}")
    if len(p80)>=2:
        stride = p80[1]-p80[0]
        log(f"Record stride: {stride}")
    log("\nHex dump:"); log(hexdump(dd[:0x160], 0x3C0700))

    log("\n"+"="*70); log("FINAL SUMMARY"); log("="*70)
    log(f"Confirmed font: Resource 1272 (65,792B, 256x512 PSMT4)")
    log(f"PSMT4 > 30KB: {len(psmt4_big)}")
    log(f"PSMT4 grayscale CLUT: {len(gray_fonts)}")
    log("\nFONT ATLAS LIST:")
    for idx,fs,ti,fn,vals in gray_fonts:
        role = "CONFIRMED main font" if idx==1272 else "LIKELY font atlas"
        log(f"  Resource {idx:4d}: {fs:8d}B {ti[wk]}x{ti[hk]} PSMT4 - {role}")
    if len(gray_fonts) <= 1:
        log("  Only 1 grayscale PSMT4. Checking PSMT8 neighbors...")
        for entry in manifest:
            if entry.get("skipped"): continue
            idx = entry["index"]
            if not (1265<=idx<=1285): continue
            fp = os.path.join(RESDIR, entry["filename"])
            if not os.path.exists(fp): continue
            fs = os.path.getsize(fp)
            with open(fp,"rb") as f: hd=f.read(192); f.seek(max(0,fs-1024)); tail=f.read(1024)
            if not is_gs_header(hd): continue
            ti = parse_tex0(hd)
            if ti.get("psm") == 19 and len(tail)>=1024:
                is_gray = all(tail[i*4]==tail[i*4+1]==tail[i*4+2] for i in range(min(256,len(tail)//4)))
                if is_gray:
                    log(f"  Res {idx}: {fs}B {ti[wk]}x{ti[hk]} PSMT8 GRAYSCALE!")

    os.makedirs(OUTDIR, exist_ok=True)
    fp = os.path.join(OUTDIR, "FINDINGS.md")
    with open(fp, "w", encoding="utf-8") as f:
        f.write("# Font Atlas Resource Search Results\n\n")
        f.write(f"Scanned {len(manifest)} resources in PACKDATA.DIG\n\n")
        f.write("```\n" + "\n".join(out) + "\n```\n")
    log(f"\nFindings written to: {fp}")

if __name__=="__main__": main()
