import json,struct
m=json.load(open('data/msg_glyph_map.json',encoding='utf-8'))
gid2c={int(k):v for k,v in m.items()}
data=open('extracted/packdata_resources/1207_type02.bin','rb').read() if __import__('os').path.exists('extracted/packdata_resources/1207_type02.bin') else None
import glob,os
f=glob.glob('extracted/packdata_resources/1207_*.bin')[0]
data=open(f,'rb').read()
off=97826
# decode 29 glyphs as BE u16
out=[]
for i in range(29):
    g=struct.unpack('>H',data[off+i*2:off+i*2+2])[0]
    out.append(gid2c.get(g,'?<%d>'%g))
s=''.join(out)
open('_lib_decode_check.txt','w',encoding='utf-8').write(s)
print('decoded 29 glyphs at off, written to file; ascii repr lens=',len(s))
print('any library char present:', 'ライブラリー' in s)
