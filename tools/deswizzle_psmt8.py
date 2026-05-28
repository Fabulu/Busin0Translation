"""
PS2 PSMT8 - close! dil32_dil4 shows tavern shape.
Try adding horizontal pixel swaps.
"""
from PIL import Image
import os


def deswizzle_palette(palette):
    result = bytearray(len(palette))
    for i in range(256):
        block = i // 32
        idx_in_block = i % 32
        if 8 <= idx_in_block < 16:
            new_idx = block * 32 + idx_in_block + 8
        elif 16 <= idx_in_block < 24:
            new_idx = block * 32 + idx_in_block - 8
        else:
            new_idx = i
        result[i*4:i*4+4] = palette[new_idx*4:new_idx*4+4]
    return result


def make_image(pixels, palette, width, height):
    img = Image.new('RGBA', (width, height))
    pal_colors = []
    for i in range(256):
        r = palette[i * 4]
        g = palette[i * 4 + 1]
        b = palette[i * 4 + 2]
        a = min(palette[i * 4 + 3] * 2, 255)
        pal_colors.append((r, g, b, a))
    img_data = [pal_colors[pixels[y * width + x]] for y in range(height) for x in range(width)]
    img.putdata(img_data)
    return img


def deinterleave_rows(data, width, height, block_h):
    out = bytearray(width * height)
    half = block_h // 2
    for bs in range(0, height, block_h):
        for y in range(block_h):
            if bs + y >= height:
                break
            src_y = bs + y
            if y < half:
                dst_y = bs + y * 2
            else:
                dst_y = bs + (y - half) * 2 + 1
            if dst_y < height:
                out[dst_y * width:(dst_y + 1) * width] = data[src_y * width:(src_y + 1) * width]
    return out


def swap_pixel_pairs(data, width, height, group_size):
    """Swap groups of pixels within each row."""
    out = bytearray(len(data))
    for y in range(height):
        for x in range(0, width, group_size * 2):
            for i in range(group_size):
                x1 = x + i
                x2 = x + group_size + i
                if x1 < width and x2 < width:
                    out[y * width + x1] = data[y * width + x2]
                    out[y * width + x2] = data[y * width + x1]
    return out


def xor_pixel_remap(data, width, height, xor_val):
    """Remap pixel x-position using XOR."""
    out = bytearray(len(data))
    for y in range(height):
        for x in range(width):
            src_x = x ^ xor_val
            if src_x < width:
                out[y * width + x] = data[y * width + src_x]
    return out


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tex_dir = os.path.join(base_dir, "build", "textures_to_edit")
    raw_path = os.path.join(tex_dir, "R2118_tavern_background.raw")

    data = open(raw_path, 'rb').read()
    width, height = 512, 512
    npix = width * height
    pix_offset = 0xD0
    pixels_raw = data[pix_offset:pix_offset + npix]
    palette_raw = data[pix_offset + npix:pix_offset + npix + 1024]
    palette = deswizzle_palette(palette_raw)

    # Apply dil32 + dil4 as baseline
    pixels = deinterleave_rows(pixels_raw, width, height, 32)
    pixels = deinterleave_rows(pixels, width, height, 4)

    # Try adding horizontal swaps
    for group in [1, 2, 4, 8]:
        p = swap_pixel_pairs(bytes(pixels), width, height, group)
        img = make_image(p, palette, width, height)
        img.save(os.path.join(tex_dir, f"R2118_dil32_dil4_swap{group}.png"))
        print(f"Saved R2118_dil32_dil4_swap{group}.png")

    # Try XOR-based x-remap
    for xor_val in [1, 2, 4, 8, 16]:
        p = xor_pixel_remap(bytes(pixels), width, height, xor_val)
        img = make_image(p, palette, width, height)
        img.save(os.path.join(tex_dir, f"R2118_dil32_dil4_xor{xor_val}.png"))
        print(f"Saved R2118_dil32_dil4_xor{xor_val}.png")

    # Also try dil32_dil8
    pixels8 = deinterleave_rows(pixels_raw, width, height, 32)
    pixels8 = deinterleave_rows(pixels8, width, height, 8)
    img = make_image(pixels8, palette, width, height)
    img.save(os.path.join(tex_dir, "R2118_dil32_dil8.png"))
    print("Saved R2118_dil32_dil8.png")

    # Try triple: dil32_dil8_dil2
    pixels82 = deinterleave_rows(pixels8, width, height, 2)
    img = make_image(pixels82, palette, width, height)
    img.save(os.path.join(tex_dir, "R2118_dil32_dil8_dil2.png"))
    print("Saved R2118_dil32_dil8_dil2.png")

    # Try dil32_dil4_dil2
    pixels42 = deinterleave_rows(pixels, width, height, 2)
    img = make_image(pixels42, palette, width, height)
    img.save(os.path.join(tex_dir, "R2118_dil32_dil4_dil2.png"))
    print("Saved R2118_dil32_dil4_dil2.png")


if __name__ == "__main__":
    main()
