import struct, sys, zstandard, io
def extract_member(path, want):
    with open(path,'rb') as f: data=f.read()
    off=0; out={}
    while off+4 <= len(data):
        if data[off:off+4] != b'PK\x03\x04': break
        method,=struct.unpack_from('<H', data, off+8)
        csize,usize=struct.unpack_from('<II', data, off+18)
        fnlen,eflen=struct.unpack_from('<HH', data, off+26)
        name=data[off+30:off+30+fnlen].decode('latin1')
        body_off=off+30+fnlen+eflen
        comp=data[body_off:body_off+csize]
        if want is None or want in name:
            if method==93:
                dctx=zstandard.ZstdDecompressor()
                try: raw=dctx.decompress(comp, max_output_size=33554432)
                except Exception: raw=dctx.stream_reader(io.BytesIO(comp)).read()
                out[name]=raw
            elif method==0: out[name]=comp
        off=body_off+csize
    return out
if __name__=='__main__':
    path=sys.argv[1]; want=sys.argv[2] if len(sys.argv)>2 else None
    outdir=sys.argv[3] if len(sys.argv)>3 else '_q7'
    for n,b in extract_member(path, want).items():
        outp=outdir+'/'+n.replace(' ','_').replace('/','_')
        open(outp,'wb').write(b); print(n, len(b), '->', outp)
