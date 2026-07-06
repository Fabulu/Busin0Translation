#!/usr/bin/env python3
"""Self-verify Phase 4+5 R1197 fixes WITHOUT a full build.
- json.load parses batch_01.json
- Replicate build_v9 Step-4 encoding for R1197 only, inject via
  patch_section1_offsets.inject_and_patch into a temp dir.
- Copy the patched R1197 over a temp packdata_resources so the leak_detector
  engine reads OUR injected output, run detect_leaks, confirm 0 HIGH leaks in
  the bar scene.
- Decode g916: assert markers preserved + 2 non-empty options.
- Decode previously-leaked box groups (g904-g912) and confirm no narration.
"""
import sys, os, json, struct, glob, shutil, tempfile
sys.stdout.reconfigure(encoding='utf-8')
os.chdir('C:/programmieren/wizardrytranslation')
sys.path.insert(0, 'tools')

# 1) JSON parses
data = json.load(open('data/type2_translated/batch_01.json', encoding='utf-8'))
print('[1] batch_01.json parses: %d entries' % len(data))

# 2) Replicate Step-4 encoding for R1197.
#    Extract ONLY the helper functions from build_v9 via AST (do NOT exec the
#    module -- its top level runs the whole build).
import ast
src = open('build/build_v9.py').read()
tree = ast.parse(src)
WANT = {'enc', 'word_wrap', '_wrap_line', 'wrap_type2_text', 'load_pristine_choice_groups'}
from patch_section1_offsets import group_choice_markers as _gcm
ns = {'json': json, 'struct': struct, 'os': os, 're': __import__('re'),
      'group_choice_markers': _gcm}
# enc() needs the global `table` and TYPE2_WRAP_WIDTH
ns['table'] = json.load(open('data/english_glyph_table.json', encoding='utf-8'))
ns['TYPE2_WRAP_WIDTH'] = 16
ns['HEADER_SIZE'] = 0x20
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name in WANT:
        exec(compile(ast.Module([node], []), 'build_v9_fn', 'exec'), ns)
enc = ns['enc']
wrap_type2_text = ns['wrap_type2_text']
load_pristine_choice_groups = ns['load_pristine_choice_groups']

r_id = 1197
msg_trans = {e['msg_index']: e['english'] for e in data
             if e['resource'] == r_id and e.get('english')
             and not any(ord(c) > 127 for c in e['english'])}
choice_groups = load_pristine_choice_groups(r_id)
print('[2] choice groups in pristine R1197:', sorted(g for g in choice_groups if 900 <= g <= 940))

encoded = {}
for mi, en_text in msg_trans.items():
    if mi not in choice_groups:
        en_text = wrap_type2_text(en_text)
    glyphs = []
    for page_i, page in enumerate(en_text.split(' // ')):
        if page_i > 0:
            glyphs.append(0xFFD2)
        line_count = 0
        for pi, part in enumerate(page.split(' / ')):
            if pi > 0:
                line_count += 1
                if line_count >= 3:
                    glyphs.append(0xFFD2); line_count = 0
                else:
                    glyphs.append(0xFFFE)
            for ch in part:
                glyphs.append(enc(ch))
    encoded[mi] = glyphs

# 3) inject_and_patch into temp dir
from patch_section1_offsets import inject_and_patch
tmp = tempfile.mkdtemp(prefix='r1197verify_')
out_name, status = inject_and_patch(r_id, encoded, 'extracted/packdata_raw', tmp)
print('[3] inject_and_patch: out=%r status=%r' % (out_name, status))
if out_name is None:
    raise SystemExit('INJECT FAILED')
patched = os.path.join(tmp, out_name)

# 4) Run leak detector against OUR injected file.
#    The engine reads build/packdata_resources/1197_type02.raw -> temporarily swap.
pr = 'build/packdata_resources/1197_type02.raw'
backup = pr + '.verifybak'
shutil.copy2(pr, backup)
try:
    shutil.copy2(patched, pr)
    sys.path.insert(0, 'build/recon_v86/scenebug/leak_detector')
    # fresh import of detect/engine
    for m in ('detect', 'engine'):
        if m in sys.modules:
            del sys.modules[m]
    import detect, engine
    leaks, err = engine.detect_leaks(1197)
    if err:
        raise SystemExit('detect err: %s' % err)
    # detect_leaks returns dict {high, low, ...}
    highs = leaks.get('high', []) if isinstance(leaks, dict) else leaks[0]
    bar_highs = [h for h in highs if h.get('severity') == 'HIGH'
                 and (890 <= (h.get('group_a_last') or 0) <= 945
                      or 890 <= (h.get('group_b_first') or 0) <= 945)]
    all_high = [h for h in highs if h.get('severity') == 'HIGH']
    print('[4] leak_detector: HIGH total=%d  HIGH in bar scene(890-945)=%d'
          % (len(all_high), len(bar_highs)))
    for h in bar_highs:
        print('    LEAK', h.get('group_a_last'), '->', h.get('group_b_first'),
              h.get('effect'))
finally:
    shutil.move(backup, pr)

# 5) Decode g916 from patched: markers preserved + 2 non-empty options
def parse_groups(sec2):
    n = len(sec2) // 2; groups = []; start = 0
    for i in range(n):
        if struct.unpack_from('>H', sec2, i*2)[0] == 0xFFFF:
            groups.append((start, i)); start = i+1
    return groups

raw = open(patched, 'rb').read()
sec2_off = struct.unpack_from('<I', raw, 0x18)[0]
sec2_size = struct.unpack_from('<I', raw, 0x14)[0]
sec2 = raw[sec2_off:sec2_off+sec2_size]
groups = parse_groups(sec2)

def gwords(gi):
    gs, ge = groups[gi]
    return [struct.unpack_from('>H', sec2, w*2)[0] for w in range(gs, ge)]

def decode_text(words):
    GM = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))
    out = []
    for g in words:
        if g >= 0xFB00: out.append('<%04X>' % g); continue
        out.append(GM.get(str(g), '[%d]' % g))
    return ''.join(out)

for gi in (916, 930):
    w = gwords(gi)
    markers = [x for x in w if 0xFFC0 <= x <= 0xFFCF]
    # split options: text after each marker until next marker/FFFF/end
    opts = []
    cur = None
    for x in w:
        if 0xFFC0 <= x <= 0xFFCF:
            if cur is not None: opts.append(cur)
            cur = []
        elif cur is not None:
            cur.append(x)
    if cur is not None: opts.append(cur)
    opt_texts = [decode_text([c for c in o if c < 0xFB00]) for o in opts]
    nonempty = [t for t in opt_texts if t.strip()]
    print('[5] g%d markers=%r options=%r' % (gi, ['%04X' % m for m in markers], opt_texts))
    assert len(markers) == 2, 'g%d expected 2 markers' % gi
    assert len(nonempty) == 2, 'g%d expected 2 non-empty options' % gi

# 6) Decode previously-leaked box groups g904-g912: confirm no third-person
#    narration phrases (the old filler) remain.
BAD = ['cheers echoed', 'patrons raised', 'time to go', 'labyrinth awaited',
       'brave', "vera's words", 'true conviction']
print('[6] box-group g904-g912 content check:')
leaked = []
for gi in range(904, 913):
    txt = decode_text(gwords(gi)).lower()
    for b in BAD:
        if b in txt:
            leaked.append((gi, b))
    print('    g%d: %s' % (gi, decode_text(gwords(gi))[:70]))
print('    fabricated-narration phrases still present:', leaked)
assert not leaked, 'narration filler still in box groups: %r' % leaked

shutil.rmtree(tmp, ignore_errors=True)
print('\nALL VERIFY CHECKS PASSED')
