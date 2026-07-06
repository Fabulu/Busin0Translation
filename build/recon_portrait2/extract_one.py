import zipfile, zstandard, struct, sys, os
sys.stdout.reconfigure(encoding='utf-8')

def raw_member_bytes(path, name):
    z = zipfile.ZipFile(path)
    info = z.getinfo(name)
    with open(path,'rb') as fh:
        fh.seek(info.header_offset)
        hdr = fh.read(30)
        n = struct.unpack('<H', hdr[26:28])[0]
        m = struct.unpack('<H', hdr[28:30])[0]
        fh.seek(info.header_offset + 30 + n + m)
        return fh.read(info.compress_size), info.file_size, info.compress_type

def extract(path, name, out):
    raw, fsize, ctype = raw_member_bytes(path, name)
    if raw[:4] == b'\x28\xb5\x2f\xfd':
        dctx = zstandard.ZstdDecompressor()
        # streaming decompress (no content size in frame)
        data = dctx.stream_reader(raw).read()
        with open(out,'wb') as f: f.write(data)
        return len(data), 'zstd'
    else:
        # maybe stored/deflate fallback
        z = zipfile.ZipFile(path)
        data = z.read(name)
        with open(out,'wb') as f: f.write(data)
        return len(data), 'zipfile'

if __name__=='__main__':
    path, name, out = sys.argv[1], sys.argv[2], sys.argv[3]
    n, how = extract(path, name, out)
    print(f'wrote {out} {n} bytes via {how}')
