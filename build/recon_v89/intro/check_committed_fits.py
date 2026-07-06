import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools')
from strip_patcher import load_font
# Load committed (HEAD) labels
import subprocess
cfg=json.loads(subprocess.check_output(['git','show','HEAD:data/strip_labels/r2880_prologue.json']).decode('utf-8'))
lay=cfg['layout']; lines=cfg['lines']; caps=lay['line_caps']
base=lay['font_size']; gmax=lay['max_line_width']
print("Committed (HEAD) per-line-cap LEFT-ALIGN layout — does each line fit its UV cap?")
allok=True
for i,ln in enumerate(lines):
    text=ln['en']; cap=min(ln.get('cap',caps[i]),gmax); size=base
    font=load_font(size,bold=True)
    while font.getbbox(text)[2]-font.getbbox(text)[0]>cap and size>12:
        size-=1; font=load_font(size,bold=True)
    w=font.getbbox(text)[2]-font.getbbox(text)[0]
    fit = w<=cap
    allok &= fit
    print(f"  i={i:2} cap={cap:3} size={size:2} w={w:3} {'OK' if fit else 'OVERFLOW'}  {text[:42]}")
print("ALL FIT" if allok else "SOME OVERFLOW (would clip even in committed layout)")
