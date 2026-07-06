import sys,struct,json
sys.stdout.reconfigure(encoding='utf-8')
# R1892 Vera record: derive exact romanization. Vera katakana nv = 273,270,93,231
# To romanize IN R1892 (LE): write ascii name_val = ascii_gid+95 as LE u16.
gt=json.load(open('data/english_glyph_table.json',encoding='utf-8'))
def gid(c): return gt.get(c, gt.get(c.lower(),31))
for name in ['Vera','Erika','Konde','Iris','Aoi']:
    vals=[gid(c)+95 for c in name]
    print('%-8s ascii name_vals(+95)=%s  LE bytes=%s'%(name,vals,b''.join(struct.pack('<H',v) for v in vals).hex()))
# Confirm R1892 stride/where Vera name sits for patcher
b=open('extracted/packdata_raw/1892_type20.raw','rb').read()
print()
print('R1892: Vera name run @0xBF2:', b[0xBF2:0xBF2+12].hex())
print('  record index byte @0xBF0:', b[0xBF0:0xBF2].hex())
# How does name terminate? show bytes after
print('  after name @0xBFA..:', b[0xBFA:0xC0A].hex())
