# Manual trace of float branch 0x3097b0-0x3097dc
# 0x3097b0: lui   $v0, 0x3e75
# 0x3097b4: mtc1  $s3, $f0      (44 93 00 00: mtc1 rt=$19=s3 -> f0)   [glyph code]
# 0x3097b8: ori   $v1, $v0, 0xc28f   -> $v1 = 0x3e75c28f = 0.24f (as int bits)
# 0x3097bc: mtc1  $v1, $f1      (44 83 08 00: mtc1 rt=$3=v1 -> f1)    [0.24]
# 0x3097c0: lh    $v0, 0x1ce($sp)    [current X]
# 0x3097c4: cvt.s.w $f0,$f0          f0 = (float)glyph_code
# 0x3097c8: mul.s   $f0,$f1,$f0      f0 = 0.24 * glyph_code
# 0x3097cc: cvt.w.s $f0,$f0          f0 = (int)(0.24*glyph_code)
# 0x3097d0: mfc1    $v1,$f0          v1 = that int
# 0x3097d8: addu    $v0,$v0,$v1      X = X + 0.24*glyph_code
# 0x3097dc: sh      $v0,0x1ce($sp)
print("Float branch: X += (int)(0.24 * glyph_code_s3)")
print("0.24 const at 0x3097b0(lui 0x3e75)/0x3097b8(ori 0xc28f) = 0x3e75c28f")
