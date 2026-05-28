import struct, json, os

os.chdir('C:/Programmieren/wizardrytranslation')
gmap = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))

# Study how the decoder actually works by looking at the existing code
# First check the raw files that exist
translated_t1 = [34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,720,1053,1908,2124,2654]

for rid in translated_t1[:8]:
    for tc in [1, 2]:
        fname = f"{rid:04d}_type{tc:02d}.raw"
        path = f'extracted/packdata_raw/{fname}'
        if os.path.exists(path):
            data = open(path, 'rb').read()
            hexdump = ' '.join(f'{b:02X}' for b in data[:64])
            print(f"R{rid} type{tc:02d}: {len(data)} bytes")
            print(f"  {hexdump}")
            # Show offset 16 area more carefully
            if len(data) >= 32:
                vals = []
                for j in range(0, min(64, len(data)), 4):
                    v = struct.unpack_from('>I', data, j)[0]
                    vals.append(f'{v:08X}')
                print(f"  BE32: {' '.join(vals)}")
            print()
