# Findings: Untranslated MSG Resources 2478-2876

## Overview

- **Total target indices scanned**: 180
- **MSG (type01) resources found**: 173
- **Resources with extractable text**: 58
- **Resources with NO text (binary only)**: 115
- **Total text messages extracted**: 495
- **Non-MSG resources skipped**: 7

## Resource Structure

All resources share a common layout:

1. **16-byte header**: Sequential table entry (always `01 00 00 00 02 00 00 00 ...`)
2. **82-byte config block**: Display/rendering parameters
3. **Triple-FFFF** at offset 98: Header separator
4. **Binary data block** (variable size): Likely image/texture data embedded in the MSG resource
5. **Text messages**: FFFF-delimited glyph streams (at end of resource)

### Size Distribution

| Size | Count | With Text |
|------|-------|-----------|
| 480B | 1 | 0 |
| 736B | 8 | 0 |
| 2,272B | 2 | 0 |
| 5,280B | 1 | 1 |
| 8,416B | 2 | 0 |
| 34,880B | 1 | 1 |
| 66,720B | 102 | 44 |
| 70,736B | 1 | 1 |
| 132,256B | 55 | 11 |

## Category Distribution

| Category | Count |
|----------|-------|
| empty_or_binary | 115 |
| single_kanji_labels | 21 |
| short_labels | 16 |
| description_text | 12 |
| dialogue | 4 |
| system_or_label | 3 |
| name_list | 2 |

## Range Analysis

### Resources 2478-2500 (23 resources, 2 with text, 26 messages)

- empty_or_binary: 21
- dialogue: 2

**Sample messages:**

R2478 [dialogue] (20 msgs):
```
１[64511] [62463] [3791]ビ[10481]ゴ[2556]」[2559][10]                                                                       
```
```
[65437][40959][62441][60157][29576][63736][22139][63724][1762]バ[3818]バ[8659][6][2794]la [64765] [61951]                 
```
```
[36862][64511][36856][60159][49909][55807][59330][55807][58111][55807][2814][45567][7167][36863][2815]        メ a a     
```

R2500 [dialogue] (6 msgs):
```
５
```
```
h
```
```
[64256][63743][22016] 容 ブ   ぢ [29]                                                                                      
```


### Resources 2513-2568 (50 resources, 12 with text, 44 messages)

- empty_or_binary: 38
- description_text: 7
- system_or_label: 3
- dialogue: 1
- short_labels: 1

**Sample messages:**

R2515 [dialogue] (12 msgs):
```
[28909][58360][65328][52477][64768][58407][63487][62464][16127][64512][1535][65153]ビ                                    
```
```
ツ[65279]レ[12529][65319]                                                                                                 
```
```
[62718][54012][42526][3834][42510][14580][44936][19441][46695][64880][3720][64805][6289][63032][33462][62524][35019][106
```

R2517 [description_text] (3 msgs):
```
ゴ[64767]ぐ[63998][7][63741] [65276][62208][65018][61184][65268][9728]                                                    
```
```
 | [64252][61950][61439][65355][2826][17710][4608][21543][6400][10002][9286][5930][64004][11879][49165][13927][17169][1775
```
```
[63806][64767][64172][61183][65015][58111][46586][58622][61439][65464][61951][65330][1026][5901][4608][4363][4608][17175
```

R2521 [system_or_label] (1 msgs):
```
 [64767] [2559] バ 
```

R2523 [short_labels] (1 msgs):
```
別
```


### Resources 2579-2579 (1 resources, 0 with text, 0 messages)

- empty_or_binary: 1

**Sample messages:**


### Resources 2778-2876 (99 resources, 44 with text, 425 messages)

- empty_or_binary: 55
- single_kanji_labels: 21
- short_labels: 15
- description_text: 5
- name_list: 2
- dialogue: 1

**Sample messages:**

R2783 [description_text] (1 msgs):
```
[15529][44016][65261][36779][35283]別[48608][3840][49552][1536][51985] [52709]せ[26332][96][8933][4][20157][6]            
```

R2788 [description_text] (1 msgs):
```
[63485][57834][63480][57835][63468][43758][61930]レ[65258][61414][64748][60131][63982][59613][64234][59037]９[32] ９    [64
```

R2791 [single_kanji_labels] (10 msgs):
```
難
```
```
良
```
```
王
```

R2793 [description_text] (2 msgs):
```
[39616][63999][44436][58879][63487][60637][63483][59872][63226][58604][63478][54513][46572][63988][53476][63478][62439][
```
```
[63706][65432][65278][54879][60922][40448]                                                                              
```


## Key Findings

### 1. Most resources are hybrid image+text containers

The 132KB and 66KB resources contain a large binary data block (likely texture/image data)
with text messages appended at the end. This is different from pure dialogue resources.

### 2. The 2778-2876 block contains mostly single-kanji labels

After filtering out header noise, the 66KB resources in this range contain:
- Single kanji characters used as labels (e.g., menu items, status labels)
- Short text fragments, often 1-3 characters
- Very few full sentences or dialogue lines

This suggests these are **UI/menu screen resources** with embedded graphics
and text overlays, NOT dialogue or spell/item descriptions.

### 3. The 2478-2568 range contains larger image resources

The 132KB resources have ~22-54KB of binary data before any text appears.
The text content is sparse and heavily mixed with unmapped glyph IDs.
These may be **scene/event resources** combining background images with text overlays.

### 4. Small resources (2579, 2560, etc.) have more text content

Resources like R2560 (2,272B) and R2579 (8,416B) have minimal binary headers
and more text content, suggesting they are closer to pure text resources.

### 5. Many glyphs remain unmapped

Most frequent unmapped glyph IDs in decoded text:

| Glyph ID | Occurrences |
|----------|-------------|
| 65280 | 39 |
| 4 | 35 |
| 1024 | 26 |
| 7424 | 25 |
| 2 | 23 |
| 65279 | 22 |
| 12 | 21 |
| 65023 | 18 |
| 64511 | 16 |
| 3840 | 16 |
| 34048 | 15 |
| 2304 | 15 |
| 105 | 14 |
| 32768 | 14 |
| 64767 | 13 |

These unmapped IDs may represent additional kanji needed for the glyph map.

## Conclusion

The 2478-2876 resource block at the end of PACKDATA does NOT contain:
- Spell descriptions (no significant spell-related text found)
- Item descriptions (no significant item-related text found)
- Late-game dialogue (no coherent dialogue passages found)

Instead, these appear to be **UI/screen layout resources** that combine:
- Embedded image/texture data (the large binary blocks)
- Short text labels for UI elements (single kanji, menu items)
- Possibly HUD or status screen overlays

The text content is minimal and consists mainly of single-character labels.
Translation priority for this block should be **LOW** compared to dialogue resources.

## Full decoded output

See: `data/untranslated_2478_2876.txt`
