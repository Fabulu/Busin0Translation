# ISO Diff Report: v15 EN vs Original JP
JP: C:/Programmieren/wizardrytranslation/Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso
EN: C:/Programmieren/wizardrytranslation/build/BUSIN0_EN_v15.iso

JP PACKDATA.DIG: LBA=16029, size=839,661,568
EN PACKDATA.DIG: LBA=16029, size=839,843,840

## TOC entries
R38 JP TOC: sector_off=0x7AD, sectors=4, type=1
R38 EN TOC: sector_off=0x7AE, sectors=6, type=1
R1272 JP TOC: sector_off=0x3395C, sectors=33, type=1
R1272 EN TOC: sector_off=0x339AB, sectors=33, type=1

## R38 (MSG resource)
JP size: 8,192 bytes
EN size: 12,288 bytes
**SIZE DIFFERS** (JP=8,192 vs EN=12,288)
Result: **DIFFERENT** - at least 1,000+ differing bytes in first 8,192 bytes

First 10 differing bytes:
| Offset | JP byte | EN byte |
|--------|---------|---------|
| 0x00000004 | 0x58 | 0x10 |
| 0x00000005 | 0x1D | 0x2B |
| 0x00000025 | 0x1A | 0x1C |
| 0x00000029 | 0x24 | 0x26 |
| 0x0000002D | 0x2E | 0x30 |
| 0x00000031 | 0x38 | 0x3A |
| 0x00000035 | 0x42 | 0x44 |
| 0x00000039 | 0x4A | 0x50 |
| 0x0000003D | 0x54 | 0x5E |
| 0x00000041 | 0x5C | 0x6A |

## R1272 (font atlas)
JP size: 67,584 bytes
EN size: 67,584 bytes
Result: **DIFFERENT** - at least 1,000+ differing bytes in first 67,584 bytes

First 10 differing bytes:
| Offset | JP byte | EN byte |
|--------|---------|---------|
| 0x00000183 | 0xFF | 0xF6 |
| 0x00000188 | 0xFF | 0xB8 |
| 0x000001D8 | 0xFF | 0x4F |
| 0x000001D9 | 0xFF | 0xFC |
| 0x000001DE | 0xFF | 0xB5 |
| 0x000001DF | 0xFF | 0xD3 |
| 0x000001E4 | 0xFF | 0xAB |
| 0x000001E5 | 0xFF | 0xAA |
| 0x000001EA | 0xFF | 0xDF |
| 0x000001EB | 0xFF | 0xF8 |

JP EXE: LBA=457143, size=4,185,776
EN EXE: LBA=457143, size=4,185,776

## SLPM_653.78 (EXE)
JP size: 4,185,776 bytes
EN size: 4,185,776 bytes
Result: **DIFFERENT** - 154 differing bytes (+ 0 extra bytes from size diff)

First 10 differing bytes:
| Offset | JP byte | EN byte |
|--------|---------|---------|
| 0x003C93B0 | 0xC4 | 0x25 |
| 0x003C93B2 | 0xE0 | 0x4D |
| 0x003C93B4 | 0x5D | 0x49 |
| 0x003C93B6 | 0xE8 | 0x4C |
| 0x003C93B8 | 0xC1 | 0x49 |
| 0x003C93BA | 0xFF | 0x41 |
| 0x003C93BB | 0xFF | 0x00 |
| 0x003C93C0 | 0xE8 | 0x2C |
| 0x003C93C2 | 0x09 | 0x55 |
| 0x003C93C3 | 0x01 | 0x00 |

## Full PACKDATA resource scan
  R34: DIFFERS (JP 69,632 vs EN 69,632 bytes)
  R35: DIFFERS (JP 4,096 vs EN 4,096 bytes)
  R36: DIFFERS (JP 4,096 vs EN 6,144 bytes)
  R37: DIFFERS (JP 4,096 vs EN 4,096 bytes)
  R38: DIFFERS (JP 8,192 vs EN 12,288 bytes)
  R40: DIFFERS (JP 4,096 vs EN 6,144 bytes)
  R41: DIFFERS (JP 2,048 vs EN 4,096 bytes)
  R42: DIFFERS (JP 2,048 vs EN 4,096 bytes)
  R43: DIFFERS (JP 2,048 vs EN 4,096 bytes)
  R44: DIFFERS (JP 4,096 vs EN 6,144 bytes)
  R45: DIFFERS (JP 8,192 vs EN 12,288 bytes)
  R46: DIFFERS (JP 22,528 vs EN 24,576 bytes)
  R47: DIFFERS (JP 4,096 vs EN 6,144 bytes)
  R48: DIFFERS (JP 4,096 vs EN 8,192 bytes)
  R49: DIFFERS (JP 4,096 vs EN 8,192 bytes)
  R989: DIFFERS (JP 626,688 vs EN 550,912 bytes)
  R990: DIFFERS (JP 626,688 vs EN 624,640 bytes)
  R1034: DIFFERS (JP 632,832 vs EN 573,440 bytes)
  R1053: DIFFERS (JP 38,912 vs EN 40,960 bytes)
  R1193: DIFFERS (JP 6,144 vs EN 6,144 bytes)
  R1194: DIFFERS (JP 8,192 vs EN 10,240 bytes)
  R1196: DIFFERS (JP 106,496 vs EN 133,120 bytes)
  R1197: DIFFERS (JP 116,736 vs EN 137,216 bytes)
  R1198: DIFFERS (JP 20,480 vs EN 24,576 bytes)
  R1199: DIFFERS (JP 36,864 vs EN 45,056 bytes)
  R1200: DIFFERS (JP 47,104 vs EN 55,296 bytes)
  R1201: DIFFERS (JP 26,624 vs EN 34,816 bytes)
  R1202: DIFFERS (JP 49,152 vs EN 61,440 bytes)
  R1203: DIFFERS (JP 169,984 vs EN 223,232 bytes)
  R1204: DIFFERS (JP 110,592 vs EN 135,168 bytes)

Total: 50 resources differ, 2831 identical (of 2881 valid)
