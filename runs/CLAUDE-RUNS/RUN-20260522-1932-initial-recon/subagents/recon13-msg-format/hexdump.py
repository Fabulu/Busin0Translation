import sys, struct, os

def hexdump(data, offset=0, length=None):
    if length is None:
        length = len(data)
    end = min(offset + length, len(data))
    for i in range(offset, end, 16):
        hex_part = ' '.join(f'{data[j]:02x}' for j in range(i, min(i+16, end)))
        ascii_part = ''.join(chr(data[j]) if 32 <= data[j] < 127 else '.' for j in range(i, min(i+16, end)))
        print(f'{i:08x}  {hex_part:<48s}  |{ascii_part}|')

files = [
    'C:/Programmieren/wizardrytranslation/extracted_busin1/IMAGE/EVENT/UEDA.MSG',
    'C:/Programmieren/wizardrytranslation/extracted_busin1/IMAGE/EVENT/KYOUGOKU.MSG',
    'C:/Programmieren/wizardrytranslation/extracted_busin1/IMAGE/EVENT/FUKAUMI.MSG',
]

for fpath in files:
    data = open(fpath, 'rb').read()
    fname = os.path.basename(fpath)
    fsize = len(data)
    print(f'=== {fname} ({fsize} bytes) ===')
    print(f'--- First 256 bytes ---')
    hexdump(data, 0, 256)
    print(f'--- Bytes 256-512 ---')
    hexdump(data, 256, 256)
    print(f'--- Bytes 512-768 ---')
    hexdump(data, 512, 256)
    print(f'--- Bytes 1024-1280 ---')
    hexdump(data, 1024, 256)
    print(f'--- Bytes 2048-2304 ---')
    hexdump(data, 2048, 256)
    print(f'--- Bytes 4096-4352 ---')
    hexdump(data, 4096, 256)
    print(f'--- Last 256 bytes ---')
    hexdump(data, max(0, fsize-256), 256)
    print()
