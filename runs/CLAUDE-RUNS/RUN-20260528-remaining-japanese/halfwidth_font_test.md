# Halfwidth Font Feasibility Test
Date: 2026-05-28

## Question
Can readable English text fit in 6 pixels wide per character?

## Results Summary

| Font | Size | MaxW | MaxH | <=6px | <=7px | <=8px |
|------|------|------|------|-------|-------|-------|
| Arial | 5 | 5 | 7 | YES | YES | YES |
| Arial | 6 | 6 | 8 | YES | YES | YES |
| Arial | 7 | 7 | 9 | no (2) | YES | YES |
| Arial | 8 | 8 | 10 | no (5) | no (2) | YES |
| Arial | 9 | 9 | 11 | no (11) | no (3) | no (2) |
| Arial | 10 | 10 | 12 | no (25) | no (10) | no (3) |
| Consolas | 5 | 3 | 6 | YES | YES | YES |
| Consolas | 6 | 4 | 7 | YES | YES | YES |
| Consolas | 7 | 4 | 8 | YES | YES | YES |
| Consolas | 8 | 5 | 8 | YES | YES | YES |
| Consolas | 9 | 5 | 9 | YES | YES | YES |
| Consolas | 10 | 6 | 10 | YES | YES | YES |
| Courier New | 5 | 3 | 7 | YES | YES | YES |
| Courier New | 6 | 4 | 7 | YES | YES | YES |
| Courier New | 7 | 5 | 8 | YES | YES | YES |
| Courier New | 8 | 5 | 10 | YES | YES | YES |
| Courier New | 9 | 6 | 10 | YES | YES | YES |
| Courier New | 10 | 6 | 12 | YES | YES | YES |
| Lucida Console | 5 | 3 | 5 | YES | YES | YES |
| Lucida Console | 6 | 4 | 6 | YES | YES | YES |
| Lucida Console | 7 | 4 | 8 | YES | YES | YES |
| Lucida Console | 8 | 5 | 9 | YES | YES | YES |
| Lucida Console | 9 | 6 | 10 | YES | YES | YES |
| Lucida Console | 10 | 7 | 10 | no (2) | YES | YES |
| Segoe UI | 5 | 5 | 8 | YES | YES | YES |
| Segoe UI | 6 | 6 | 9 | YES | YES | YES |
| Segoe UI | 7 | 7 | 10 | no (2) | YES | YES |
| Segoe UI | 8 | 8 | 11 | no (7) | no (1) | YES |
| Segoe UI | 9 | 9 | 12 | no (9) | no (6) | no (1) |
| Segoe UI | 10 | 10 | 13 | no (16) | no (9) | no (3) |
| Tahoma | 5 | 5 | 7 | YES | YES | YES |
| Tahoma | 6 | 6 | 8 | YES | YES | YES |
| Tahoma | 7 | 7 | 9 | no (2) | YES | YES |
| Tahoma | 8 | 8 | 10 | no (4) | no (2) | YES |
| Tahoma | 9 | 9 | 11 | no (9) | no (3) | no (1) |
| Tahoma | 10 | 10 | 12 | no (20) | no (5) | no (3) |
| Verdana | 5 | 5 | 8 | YES | YES | YES |
| Verdana | 6 | 6 | 9 | YES | YES | YES |
| Verdana | 7 | 8 | 10 | no (4) | no (1) | YES |
| Verdana | 8 | 9 | 11 | no (5) | no (4) | no (1) |
| Verdana | 9 | 10 | 12 | no (20) | no (4) | no (3) |
| Verdana | 10 | 10 | 13 | no (33) | no (15) | no (4) |

## Fonts that fit ALL characters

### 6px cell width
- **Arial @ 5pt** (max glyph: 5x7px)
- **Arial @ 6pt** (max glyph: 6x8px)
- **Consolas @ 5pt** (max glyph: 3x6px)
- **Consolas @ 6pt** (max glyph: 4x7px)
- **Consolas @ 7pt** (max glyph: 4x8px)
- **Consolas @ 8pt** (max glyph: 5x8px)
- **Consolas @ 9pt** (max glyph: 5x9px)
- **Consolas @ 10pt** (max glyph: 6x10px)
- **Courier New @ 5pt** (max glyph: 3x7px)
- **Courier New @ 6pt** (max glyph: 4x7px)
- **Courier New @ 7pt** (max glyph: 5x8px)
- **Courier New @ 8pt** (max glyph: 5x10px)
- **Courier New @ 9pt** (max glyph: 6x10px)
- **Courier New @ 10pt** (max glyph: 6x12px)
- **Lucida Console @ 5pt** (max glyph: 3x5px)
- **Lucida Console @ 6pt** (max glyph: 4x6px)
- **Lucida Console @ 7pt** (max glyph: 4x8px)
- **Lucida Console @ 8pt** (max glyph: 5x9px)
- **Lucida Console @ 9pt** (max glyph: 6x10px)
- **Segoe UI @ 5pt** (max glyph: 5x8px)
- **Segoe UI @ 6pt** (max glyph: 6x9px)
- **Tahoma @ 5pt** (max glyph: 5x7px)
- **Tahoma @ 6pt** (max glyph: 6x8px)
- **Verdana @ 5pt** (max glyph: 5x8px)
- **Verdana @ 6pt** (max glyph: 6x9px)

### 7px cell width
- **Arial @ 5pt** (max glyph: 5x7px)
- **Arial @ 6pt** (max glyph: 6x8px)
- **Arial @ 7pt** (max glyph: 7x9px)
- **Consolas @ 5pt** (max glyph: 3x6px)
- **Consolas @ 6pt** (max glyph: 4x7px)
- **Consolas @ 7pt** (max glyph: 4x8px)
- **Consolas @ 8pt** (max glyph: 5x8px)
- **Consolas @ 9pt** (max glyph: 5x9px)
- **Consolas @ 10pt** (max glyph: 6x10px)
- **Courier New @ 5pt** (max glyph: 3x7px)
- **Courier New @ 6pt** (max glyph: 4x7px)
- **Courier New @ 7pt** (max glyph: 5x8px)
- **Courier New @ 8pt** (max glyph: 5x10px)
- **Courier New @ 9pt** (max glyph: 6x10px)
- **Courier New @ 10pt** (max glyph: 6x12px)
- **Lucida Console @ 5pt** (max glyph: 3x5px)
- **Lucida Console @ 6pt** (max glyph: 4x6px)
- **Lucida Console @ 7pt** (max glyph: 4x8px)
- **Lucida Console @ 8pt** (max glyph: 5x9px)
- **Lucida Console @ 9pt** (max glyph: 6x10px)
- **Lucida Console @ 10pt** (max glyph: 7x10px)
- **Segoe UI @ 5pt** (max glyph: 5x8px)
- **Segoe UI @ 6pt** (max glyph: 6x9px)
- **Segoe UI @ 7pt** (max glyph: 7x10px)
- **Tahoma @ 5pt** (max glyph: 5x7px)
- **Tahoma @ 6pt** (max glyph: 6x8px)
- **Tahoma @ 7pt** (max glyph: 7x9px)
- **Verdana @ 5pt** (max glyph: 5x8px)
- **Verdana @ 6pt** (max glyph: 6x9px)

### 8px cell width
- **Arial @ 5pt** (max glyph: 5x7px)
- **Arial @ 6pt** (max glyph: 6x8px)
- **Arial @ 7pt** (max glyph: 7x9px)
- **Arial @ 8pt** (max glyph: 8x10px)
- **Consolas @ 5pt** (max glyph: 3x6px)
- **Consolas @ 6pt** (max glyph: 4x7px)
- **Consolas @ 7pt** (max glyph: 4x8px)
- **Consolas @ 8pt** (max glyph: 5x8px)
- **Consolas @ 9pt** (max glyph: 5x9px)
- **Consolas @ 10pt** (max glyph: 6x10px)
- **Courier New @ 5pt** (max glyph: 3x7px)
- **Courier New @ 6pt** (max glyph: 4x7px)
- **Courier New @ 7pt** (max glyph: 5x8px)
- **Courier New @ 8pt** (max glyph: 5x10px)
- **Courier New @ 9pt** (max glyph: 6x10px)
- **Courier New @ 10pt** (max glyph: 6x12px)
- **Lucida Console @ 5pt** (max glyph: 3x5px)
- **Lucida Console @ 6pt** (max glyph: 4x6px)
- **Lucida Console @ 7pt** (max glyph: 4x8px)
- **Lucida Console @ 8pt** (max glyph: 5x9px)
- **Lucida Console @ 9pt** (max glyph: 6x10px)
- **Lucida Console @ 10pt** (max glyph: 7x10px)
- **Segoe UI @ 5pt** (max glyph: 5x8px)
- **Segoe UI @ 6pt** (max glyph: 6x9px)
- **Segoe UI @ 7pt** (max glyph: 7x10px)
- **Segoe UI @ 8pt** (max glyph: 8x11px)
- **Tahoma @ 5pt** (max glyph: 5x7px)
- **Tahoma @ 6pt** (max glyph: 6x8px)
- **Tahoma @ 7pt** (max glyph: 7x9px)
- **Tahoma @ 8pt** (max glyph: 8x10px)
- **Verdana @ 5pt** (max glyph: 5x8px)
- **Verdana @ 6pt** (max glyph: 6x9px)
- **Verdana @ 7pt** (max glyph: 8x10px)

## Width distribution (promising configs)

### Consolas @ 5pt (max=3px, h=6px)
- 2px: `!'),.:;]`|`
- 3px: `"#$%&(*+-/0123456789<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[^_abcdefghijklmnopqrstuvwxyz{}~`

### Courier New @ 5pt (max=3px, h=7px)
- 2px: `!'),.:;]`{|}`
- 3px: `"#$%&(*+-/0123456789<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[^_abcdefghijklmnopqrstuvwxyz~`

### Lucida Console @ 5pt (max=3px, h=5px)
- 2px: `!').:;<ijl{|`
- 3px: `"#$%&(*+,-/0123456789=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_`abcdefghkmnopqrstuvwxyz}~`

### Consolas @ 6pt (max=4px, h=7px)
- 2px: `'`|`
- 3px: `!"$()*,-./12356789:;<=>?BCEFGHIJKLNPSUZ[]^abcdehijlnpqrstuz{}`
- 4px: `#%&+04@ADMOQRTVWXY_fgkmovwxy~`

### Courier New @ 6pt (max=4px, h=7px)
- 2px: `)]|`
- 3px: `!"$&'(*,./01234578:;?@IZ[^`jsz{}`
- 4px: `#%+-69<=>ABCDEFGHJKLMNOPQRSTUVWXY_abcdefghiklmnopqrtuvwxy~`

### Lucida Console @ 6pt (max=4px, h=6px)
- 3px: `!$',.:;<>[]`ijl|`
- 4px: `"#%&()*+-/0123456789=?@ABCDEFGHIJKLMNOPQRSTUVWXYZ^_abcdefghkmnopqrstuvwxyz{}~`

### Consolas @ 7pt (max=4px, h=8px)
- 3px: `!"'(),-.:;J[]`j|`
- 4px: `#$%&*+/0123456789<=>?@ABCDEFGHIKLMNOPQRSTUVWXYZ^_abcdefghiklmnopqrstuvwxyz{}~`

### Lucida Console @ 7pt (max=4px, h=8px)
- 3px: `!$',.:;<J[]`ijl|`
- 4px: `"#%&()*+-/0123456789=>?@ABCDEFGHIKLMNOPQRSTUVWXYZ^_abcdefghkmnopqrstuvwxyz{}~`

### Arial @ 5pt (max=5px, h=7px)
- 1px: `!',.:;Iijl|`
- 2px: `"()*-/1[]`frt{}`
- 3px: `#$+023456789<=>?FJLTZ^_abcdeghknopqsuvxyz~`
- 4px: `&ABCDEGHKMNOPQRSUVXYmw`
- 5px: `%@W`

### Segoe UI @ 5pt (max=5px, h=8px)
- 1px: `!',.:;Iijl|`
- 2px: `"()*-/1?J[]`frst{}`
- 3px: `#$+023456789<=>BCEFKLPRSTXYZ^_abcdeghknopquvxyz~`
- 4px: `%&ADGHNOQUVmw`
- 5px: `@MW`

### Tahoma @ 5pt (max=5px, h=7px)
- 1px: `'il`
- 2px: `!"(),-./:;IJ[]`fjrt|`
- 3px: `$*0123456789?ABCEFKLNPSTUVXYZ_abcdeghknopqsuvxyz{}`
- 4px: `#&+<=>DGHMOQR^mw~`
- 5px: `%@W`

### Verdana @ 5pt (max=5px, h=8px)
- 1px: `'il`
- 2px: `!"(),-.:;IJ[]`fjt|`
- 3px: `$*/0123456789?EFLPYabcdeghknopqrsuvxyz{}`
- 4px: `#&+<=>ABCDGHKMNOQRSTUVXZ^_w~`
- 5px: `%@Wm`

### Courier New @ 7pt (max=5px, h=8px)
- 3px: `!'),.:;]`j{|}`
- 4px: `"#$%&(*+-/0123456789<=>?@BCDEFGHIKLNOPQSTUXYZ[^abcefghiklnoprstuvwxyz~`
- 5px: `AJMRVW_dmq`

### Consolas @ 8pt (max=5px, h=8px)
- 3px: `!',.:;`|`
- 4px: `"$()*-/12356789<=>?BCEFGHIJLNPSUZ[]^abcdehijlnpqrstuz{}`
- 5px: `#%&+04@ADKMOQRTVWXY_fgkmovwxy~`

### Courier New @ 8pt (max=5px, h=10px)
- 3px: `!'),.:;]|`
- 4px: `"$&(*/01234578?@IZ[^`jsz{}`
- 5px: `#%+-69<=>ABCDEFGHJKLMNOPQRSTUVWXY_abcdefghiklmnopqrtuvwxy~`

### Lucida Console @ 8pt (max=5px, h=9px)
- 3px: `!',.:;]`il|`
- 4px: `"$)*+-1235BEFIJS[cdejqrsz{}`
- 5px: `#%&(/046789<=>?@ACDGHKLMNOPQRTUVWXYZ^_abfghkmnoptuvwxy~`

### Consolas @ 9pt (max=5px, h=9px)
- 3px: `'`|`
- 4px: `!"(),-.:;<J[]j{`
- 5px: `#$%&*+/0123456789=>?@ABCDEFGHIKLMNOPQRSTUVWXYZ^_abcdefghiklmnopqrstuvwxyz}~`

### Arial @ 6pt (max=6px, h=8px)
- 1px: `'ijl`
- 2px: `!"(),-./:;I[]`ft{|}`
- 3px: `*1J^cdghknqrsuvxyz`
- 4px: `#$&+023456789<=>?ABDEFHKLNPSTUVXYZ_abeop~`
- 5px: `%CGMOQRmw`
- 6px: `@W`

### Segoe UI @ 6pt (max=6px, h=9px)
- 1px: `',.:;l|`
- 2px: `!"()IJ[]`fijt{}`
- 3px: `$*-/012356789?EFLS_acehknrsuvxyz`
- 4px: `#+4<=>ABCDGHKNPRTUVXYZ^bdgopq~`
- 5px: `%&MOQmw`
- 6px: `@W`

### Tahoma @ 6pt (max=6px, h=8px)
- 1px: `'il`
- 2px: `!),-.:;I]`jt|`
- 3px: `"$(*/135?JL[acdefghnqrsuvxyz{}`
- 4px: `#+0246789<=>ABCDEFGHKNPRSTUVXYZ^_bkop~`
- 5px: `&MOQmw`
- 6px: `%@W`

### Verdana @ 6pt (max=6px, h=9px)
- 2px: `!',.:;ijl|`
- 3px: `"()-/?IJ[]`cfrstz`
- 4px: `$*0123456789ABCEFHLNPSTUVXYZ_abdeghknopquvxy{}`
- 5px: `#&+<=>DGKMOQR^w~`
- 6px: `%@Wm`

### Courier New @ 9pt (max=6px, h=10px)
- 3px: `)]|`
- 4px: `!',.:;`j{}`
- 5px: `"#$%&(*+-/0123456789<=>?@BCEHILOPQSTYZ[^abcefhilnoprstuxz~`
- 6px: `ADFGJKMNRUVWX_dgkmqvwy`

### Lucida Console @ 9pt (max=6px, h=10px)
- 4px: `!'),.:;]`ijl|`
- 5px: `"$(*-023456789>?BEGHIJLMNSUZ[^bcdeghnopqrstuz{}`
- 6px: `#%&+/1<=@ACDFKOPQRTVWXY_afkmvwxy~`

### Consolas @ 10pt (max=6px, h=10px)
- 4px: `!',.:;]`|`
- 5px: `"$()*-/12356789<=>?BCEFGHIJLNPSUZ[^abcdehijlnpqrstuz{}`
- 6px: `#%&+04@ADKMOQRTVWXY_fgkmovwxy~`

### Courier New @ 10pt (max=6px, h=12px)
- 4px: `!'),.:;]`|`
- 5px: `"$&(*/01234578?@IZ[^jsz{}`
- 6px: `#%+-69<=>ABCDEFGHJKLMNOPQRSTUVWXY_abcdefghiklmnopqrtuvwxy~`

### Arial @ 7pt (max=7px, h=9px)
- 2px: `!',./:;I[]`ijlt|`
- 3px: `"()*-1Jfr{}`
- 4px: `#$+023456789<=>?FL^_abcdeghknopqsuvxyz~`
- 5px: `&ABCDEGHKNPRSTUVXYZw`
- 6px: `%MOQm`
- 7px: `@W`

### Segoe UI @ 7pt (max=7px, h=10px)
- 2px: `!'(),.:;IJ[]`ijl{|}`
- 3px: `"*-/1?_cfrstz`
- 4px: `#$+023456789<=>BCEFKLPSTXYZ^abdeghknopquvxy`
- 5px: `ADGHNORUVw~`
- 6px: `%&MQm`
- 7px: `@W`

### Tahoma @ 7pt (max=7px, h=9px)
- 2px: `!',.:;ijl|`
- 3px: `"()-/IJ[]`frstz`
- 4px: `$*0123456789?BEFLPSXZ_abcdeghknopquvxy{}`
- 5px: `#&+<=>ACDGHKMNOQRTUVY^~`
- 6px: `@mw`
- 7px: `%W`

### Lucida Console @ 10pt (max=7px, h=10px)
- 4px: `!',.:;]il|`
- 5px: `")-25J`j{}`
- 6px: `#$%&(*+/01346789<=>?ABCDEFGHIKLMNOPQRSTUVWXYZ[^abcdefghkmnopqrstuvwxyz~`
- 7px: `@_`

### Verdana @ 7pt (max=8px, h=10px)
- 2px: `!',.:ijl|`
- 3px: `"()-/;IJ[]`ft`
- 4px: `$*0123589?FLPabcdeghnopqrsuvxyz{}`
- 5px: `467<=>ABCDEGHKNRSTUVXYZ_k`
- 6px: `#&+MOQ^w~`
- 7px: `@Wm`
- 8px: `%`

### Arial @ 8pt (max=8px, h=10px)
- 2px: `!',.:;I]`ijl|`
- 3px: `"()*-/1[frt{}`
- 4px: `J^cdghknqsuvxyz`
- 5px: `#$+023456789<=>?BEFLPSTZ_abeop~`
- 6px: `&ACDGHKNOQRUVXYw`
- 7px: `%Mm`
- 8px: `@W`

### Segoe UI @ 8pt (max=8px, h=11px)
- 2px: `!'),.:;I]`ijl|`
- 3px: `"(*-1J[frt{}`
- 4px: `$/02356789?EFLS_acehknsuvxyz`
- 5px: `#+4<=>BCGHKPRTUVXYZ^bdgopq~`
- 6px: `ADNOw`
- 7px: `%&@MQm`
- 8px: `W`

### Tahoma @ 8pt (max=8px, h=10px)
- 2px: `!',.:ijl|`
- 3px: `"()-/;IJ[]`frt`
- 4px: `$*135?Lacdeghnqsuvxyz{}`
- 5px: `0246789<ABCEFGHKNPSTUVXYZ_bkop`
- 6px: `#&+=>DMOQR^w~`
- 7px: `@m`
- 8px: `%W`

### Verdana @ 8pt (max=9px, h=11px)
- 2px: `'.il`
- 3px: `!"),:;IJ[]`jt|`
- 4px: `(-/?cfrsz`
- 5px: `$*0123456789EFLPSTYabdeghknopquvxy{}`
- 6px: `#&+<=>ABCDGHKMNOQRUVXZ^_~`
- 7px: `w`
- 8px: `@Wm`
- 9px: `%`

### Arial @ 9pt (max=9px, h=11px)
- 2px: `!',.:;I]`ijl|`
- 3px: `"()-/[ft{}`
- 4px: `*1J^r`
- 5px: `#$+023456789<=>?Labcdeghknopqsuvxyz~`
- 6px: `&ABDEFHKNPSTUVXYZ_`
- 7px: `CGMOQRmw`
- 8px: `%`
- 9px: `@W`

### Segoe UI @ 9pt (max=9px, h=12px)
- 2px: `!',.:;I]ijl|`
- 3px: `"()J[`ft{}`
- 4px: `*-/1?_acrsxz`
- 5px: `$023456789<>BEFLPSTYZbdeghknopquvy`
- 6px: `#+=ACDGHKNRUVX^~`
- 7px: `OQw`
- 8px: `%&@Mm`
- 9px: `W`

### Tahoma @ 9pt (max=9px, h=11px)
- 2px: `!'.ijl`
- 3px: `),-:;I]`t|`
- 4px: `"(/?J[cfrsz{`
- 5px: `$*0123456789EFLPSZ_abdeghknopquvxy}`
- 6px: `#+<=>ABCDGHKNRTUVXY^~`
- 7px: `&MOQmw`
- 8px: `@W`
- 9px: `%`

### Verdana @ 9pt (max=10px, h=12px)
- 2px: `'il`
- 3px: `!,.:;j|`
- 4px: `"()-/IJ[]`frt`
- 5px: `*1?acdeghnoqsuxz{}`
- 6px: `$023456789ABCEFHLNPSTUVXYZ_bkpvy`
- 7px: `#&+<=>DGKMOQR^w~`
- 8px: `m`
- 9px: `@W`
- 10px: `%`

### Arial @ 10pt (max=10px, h=12px)
- 2px: `!',.:;Iijl|`
- 3px: `()/[]`t`
- 4px: `"*-1fr{}`
- 5px: `J^cdghknqsuvxyz`
- 6px: `#$+023456789<=>?FLTZ_abeop~`
- 7px: `&ABCDEHKNPSUVXY`
- 8px: `GMOQRmw`
- 9px: `%`
- 10px: `@W`

### Segoe UI @ 10pt (max=10px, h=13px)
- 2px: `!',.:;Iijl|`
- 3px: `()J[]`{}`
- 4px: `"*-/1?frst`
- 5px: `$02356789EFLS_acehknuvxyz`
- 6px: `#+4<=>BCKPRTXYZ^bdgopq~`
- 7px: `ADGHNUV`
- 8px: `%&OQmw`
- 9px: `@M`
- 10px: `W`

### Tahoma @ 10pt (max=10px, h=12px)
- 2px: `'il`
- 3px: `!,.:;j|`
- 4px: `"()-/IJ[]`frt`
- 5px: `$*135?Lacdeghnqsuvxyz{}`
- 6px: `0246789ABCEFKNPSTUVXYZ_bkop`
- 7px: `#&+<=>DGHMOQR^~`
- 8px: `mw`
- 9px: `@W`
- 10px: `%`

### Verdana @ 10pt (max=10px, h=13px)
- 2px: `'il`
- 3px: `!,.:j|`
- 4px: `"()-;IJ[]`ft`
- 5px: `/?crsz`
- 6px: `$*0123456789EFLPabdeghknopquvxy{}`
- 7px: `<=>ABCHKNRSTUVXYZ_`
- 8px: `#&+DGMOQ^w~`
- 9px: `m`
- 10px: `%@W`

## Conclusions

### 6px width: FEASIBLE
The following fonts fit all ASCII characters in 6px:
- Arial @ 5pt
- Arial @ 6pt
- Consolas @ 5pt
- Consolas @ 6pt
- Consolas @ 7pt
- Consolas @ 8pt
- Consolas @ 9pt
- Consolas @ 10pt
- Courier New @ 5pt
- Courier New @ 6pt
- Courier New @ 7pt
- Courier New @ 8pt
- Courier New @ 9pt
- Courier New @ 10pt
- Lucida Console @ 5pt
- Lucida Console @ 6pt
- Lucida Console @ 7pt
- Lucida Console @ 8pt
- Lucida Console @ 9pt
- Segoe UI @ 5pt
- Segoe UI @ 6pt
- Tahoma @ 5pt
- Tahoma @ 6pt
- Verdana @ 5pt
- Verdana @ 6pt
However, readability at this size may be poor.

### 7px width: FEASIBLE
- Arial @ 5pt (height: 7px)
- Arial @ 6pt (height: 8px)
- Arial @ 7pt (height: 9px)
- Consolas @ 5pt (height: 6px)
- Consolas @ 6pt (height: 7px)
- Consolas @ 7pt (height: 8px)
- Consolas @ 8pt (height: 8px)
- Consolas @ 9pt (height: 9px)
- Consolas @ 10pt (height: 10px)
- Courier New @ 5pt (height: 7px)
- Courier New @ 6pt (height: 7px)
- Courier New @ 7pt (height: 8px)
- Courier New @ 8pt (height: 10px)
- Courier New @ 9pt (height: 10px)
- Courier New @ 10pt (height: 12px)
- Lucida Console @ 5pt (height: 5px)
- Lucida Console @ 6pt (height: 6px)
- Lucida Console @ 7pt (height: 8px)
- Lucida Console @ 8pt (height: 9px)
- Lucida Console @ 9pt (height: 10px)
- Lucida Console @ 10pt (height: 10px)
- Segoe UI @ 5pt (height: 8px)
- Segoe UI @ 6pt (height: 9px)
- Segoe UI @ 7pt (height: 10px)
- Tahoma @ 5pt (height: 7px)
- Tahoma @ 6pt (height: 8px)
- Tahoma @ 7pt (height: 9px)
- Verdana @ 5pt (height: 8px)
- Verdana @ 6pt (height: 9px)

### 8px width: FEASIBLE (recommended fallback)
- Arial @ 5pt (height: 7px)
- Arial @ 6pt (height: 8px)
- Arial @ 7pt (height: 9px)
- Arial @ 8pt (height: 10px)
- Consolas @ 5pt (height: 6px)
- Consolas @ 6pt (height: 7px)
- Consolas @ 7pt (height: 8px)
- Consolas @ 8pt (height: 8px)
- Consolas @ 9pt (height: 9px)
- Consolas @ 10pt (height: 10px)
- Courier New @ 5pt (height: 7px)
- Courier New @ 6pt (height: 7px)
- Courier New @ 7pt (height: 8px)
- Courier New @ 8pt (height: 10px)
- Courier New @ 9pt (height: 10px)
- Courier New @ 10pt (height: 12px)
- Lucida Console @ 5pt (height: 5px)
- Lucida Console @ 6pt (height: 6px)
- Lucida Console @ 7pt (height: 8px)
- Lucida Console @ 8pt (height: 9px)
- Lucida Console @ 9pt (height: 10px)
- Lucida Console @ 10pt (height: 10px)
- Segoe UI @ 5pt (height: 8px)
- Segoe UI @ 6pt (height: 9px)
- Segoe UI @ 7pt (height: 10px)
- Segoe UI @ 8pt (height: 11px)
- Tahoma @ 5pt (height: 7px)
- Tahoma @ 6pt (height: 8px)
- Tahoma @ 7pt (height: 9px)
- Tahoma @ 8pt (height: 10px)
- Verdana @ 5pt (height: 8px)
- Verdana @ 6pt (height: 9px)
- Verdana @ 7pt (height: 10px)

## Generated images

- `build/halfwidth_font_test.png` - Comparison atlas of all viable configs
- `build/halfwidth_font_6px.png` - Best 6px config (if any)
- `build/halfwidth_font_7px.png` - Best 7px config
- `build/halfwidth_font_8px.png` - Best 8px config