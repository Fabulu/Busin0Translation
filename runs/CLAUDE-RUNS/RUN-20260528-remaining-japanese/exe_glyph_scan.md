# EXE Remaining Japanese Glyph Scan Results

**Date:** 2026-05-28
**Scan range:** 0x3B0000 - 0x3FD000
**Method:** Consecutive aligned LE uint16 runs with >= 30% kanji density
**Total clusters found:** 617

## Skip regions (already handled)

- 0x3C3000-0x3C5300: menu structs (already handled)
- 0x3C83C0-0x3C93A0: chargen grid (R38, already handled)
- 0x3C9DA0-0x3C9DFC: name entry tab IDs (Table 2E)

## Summary by Category

| Category | Count | Offsets |
|----------|-------|--------|
| Long text string | 13 | 0x3B5DEA, 0x3B5F3E, 0x3B7A1C, 0x3B7C32, 0x3BC928 (+8 more) |
| Medium text | 391 | 0x3B6806, 0x3B6822, 0x3B6A0A, 0x3B6B5A, 0x3B6C20 (+386 more) |
| Short text | 210 | 0x3B5624, 0x3B56EC, 0x3B57F4, 0x3B58F4, 0x3B59F4 (+205 more) |
| Stat | 1 | 0x3B3D90 |
| Status effect | 2 | 0x3B3008, 0x3C9A34 |

## All Clusters

### [0] 0x3B3008-0x3B382E

- **Size:** 2086 bytes, 1043 glyphs (781 kanji)
- **Decoded:** `    (     ( ( ( 0   8   0 ( 8 (   0 ( 0   8 ( 8 0 0 8 0 0 8 8 8 @   H   @ ( H ( P   X   P ( X ( @ 0 H 0 @ 8 H 8 P 0 X 0 P 8 X 8       !"#$$%&'(()*+,--./011234556789::;<=>>?@ABCCDEFGGHIJKKLMNOOPQRSTTUVWXXYZ[\\]^_``abcdeefghiijklmmnopqqrstuuvwxyyz{|}}~♥[?96][?97][?97][?98][?99][?100][?101][?101][?102][?103][?104][?105][?105][?106][?107][?108][?108]％[?110][?111]ああいうえおおかきくけけこさししすせそたたちつてととなにぬぬねのはひひふへほほまみむめめもやゆゆよらりるるれろわわをんががぎぐげごござじずずぜぞだだぢづででどばびびぶべぼぼぱぴぷぷぺぽゃゅゅょぁぃぃぅぇぉぉっ[?192][?192]アイウウエオカカキクケケコサシシスセソソタチチツテトトナニヌヌネノハハヒフフヘホママミムムメモヤヤユヨララリルルレロワワヲンンガギギグゲゴゴザジジズゼゾゾダヂヂヅデデドバビビブベベボパパピププペポャャュョョァィィゥェェォッッヴ祠祠小手宮宮防攻攻騎使使向行行聖罰罰戦者者鎧悪悪動飾飾法魔魔辺大大王士士迷迷野神神石魔魔依兵兵飲切切奥信信忍団団回回腕開開名盗盗武炎炎算算人心心頼落落力多多臆臆法短短上賊賊言言限装装[?333]崩崩差差教中中一一気立立不事事持持悔邪邪力力骨光光女女得除除初初暗仰仰少少多紹紹外外銀場場然然情情信[?364][?364]両両影行行看看見見成与与苦苦居対対道道鉄鉄店度度転転[?380][?380]傷傷を長長二二地地[?386]重重呪呪払払[?390][?390]古報報半半彼彼戻戻教毒毒帰帰頼頼理理侍侍支水水像像集集封封告告落落願秘秘町町物物復復子子回回宿宿直直女女書[?420][?420]編編古古良良短短約約束束[?427][?427]復復上上笑笑効効時時質質紹紹れれ抜抜続続通通憶憶退退大大後後投投表表生生最最記記憶憶主主武武器器感感怪怪会会会忘忘顔顔[?457][?457]心心不不幸幸横横入入違違違隊隊[?465][?465]商商回回辺辺[?469][?469][?469]中中[?471][?471]込込[?473][?473]遺遺王王王[?476][?476]噂噂彼彼対対対[?480][?480][?481][?481][?482][?482]無無無[?484][?484]光光冒冒険険険広広刻刻息息息登登録録開開帰帰帰専専所所所出出新新兵兵兵召召喚喚能能能力力職職職地地削削除除除部部隊隊隊前前性性 (08@HPX`hpx[?96][?104]あけちのむるぐだべゅ[?192]クチノムルグダベュヴ使悪士飲開頼賊中邪暗然見店地半侍願直約質大主[?457][?465][?473][?481]刻出地種飽交間消屋色嫌受費属方箱看求突血高誰元体解街命可足幸聖美高器形内回失打先巨嘆護声穏空組草携札`
- **Purpose:** Status effect (code/early-data)
- **Hex:** `00 00 00 00 00 00 00 00 08 00 00 00 00 00 00 00 00 00 00 00 08 00 00 00 08 00 00`

### [1] 0x3B3D90-0x3B3E92

- **Size:** 258 bytes, 129 glyphs (116 kanji)
- **Decoded:** ` '.6=DLSZbipw♥[?102]％かすとひめれぐぞびぺぅエサツノミランジドピァ祠使鎧大魔忍武力言中悔除外両苦転地報頼封復[?420][?427]紹大記会横辺王[?482]広専能隊性怪交代仲追与己嫌同前度少品思看[?623]界違貴絆誰丁御仲功誓命日必高獲入美本答楽正内活響就華替巨打刻療[?832]穏部十突園法札`
- **Purpose:** Stat (code/early-data)
- **Hex:** `00 00 07 00 0e 00 16 00 1d 00 24 00 2c 00 33 00 3a 00 42 00 49 00 50 00 57 00 5f`

### [2] 0x3B5624-0x3B5630

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [3] 0x3B56EC-0x3B56F8

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [4] 0x3B57F4-0x3B5800

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [5] 0x3B58F4-0x3B5900

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [6] 0x3B59F4-0x3B5A00

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [7] 0x3B5AF4-0x3B5B00

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [8] 0x3B5BF4-0x3B5C00

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [9] 0x3B5CBC-0x3B5CC8

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [10] 0x3B5D8C-0x3B5D98

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [11] 0x3B5DEA-0x3B5E42

- **Size:** 88 bytes, 44 glyphs (21 kanji)
- **Decoded:** `ョ+ $むブ%[?108]ベ"[?96]ボ![?96]パ けピ#[?108]プ+Pペ'\ポ)nャ*nュ(nョ&\ァ,\ィ づ`
- **Purpose:** Long text string (code/early-data)
- **Hex:** `0a 01 0b 00 00 00 04 00 90 00 00 01 05 00 6c 00 01 01 02 00 60 00 02 01 01 00 60`

### [12] 0x3B5F3E-0x3B6200

- **Size:** 706 bytes, 353 glyphs (186 kanji)
- **Decoded:** `3*3(6)/',+4      ? D@0EB(GA(FC8H VWXYZ   アヴあ[?192]AZaz09[?96][?105]!/:@[`{♥[?106][?111]  !ベピンガドデパァィズゲプゴペジハヒフヘホマミムメモェォゾザダボ!ぜだづどびべぱぷぽゅぁぅぉ[?192]イエカクコシセタツトニネュ!ョポャッぞぢでばぶぼぴぺゃょぃぇっアウオキケサスソチテナヌノヂヅstゼヤユヨラリルレロワヲギグバビゥ!uwy|~[?96][?98][?100][?102][?104][?106][?108][?110]あうおきけしせたちつてとなねひほむやゆよらりるろをがぎぐげござじず[?97][?99][?101][?103][?105][?107]％[?111]いえかくさすそにのふまめぬはへみもれわんvxz}♥こ{"$&)+-/13579;=?ACEHJLMNOPQTWZ]`abcdegiklmnopqr.02468:<>@BDGIKRUX[^SVY\_fhj#%'*,F(   !"#$%&     `
- **Purpose:** Long text string (code/early-data)
- **Hex:** `13 00 0a 00 13 00 08 00 16 00 09 00 0f 00 07 00 0c 00 0b 00 14 00 00 00 00 00 00`

### [13] 0x3B6240-0x3B624C

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [14] 0x3B671C-0x3B6724

- **Size:** 8 bytes, 4 glyphs (3 kanji)
- **Decoded:** `Xあちち`
- **Purpose:** Short text (code/early-data)
- **Hex:** `38 00 70 00 80 00 80 00`

### [15] 0x3B6738-0x3B6740

- **Size:** 8 bytes, 4 glyphs (3 kanji)
- **Decoded:** `ちpちち`
- **Purpose:** Short text (code/early-data)
- **Hex:** `80 00 50 00 80 00 80 00`

### [16] 0x3B6770-0x3B6778

- **Size:** 8 bytes, 4 glyphs (2 kanji)
- **Decoded:** `X0ちち`
- **Purpose:** Short text (code/early-data)
- **Hex:** `38 00 10 00 80 00 80 00`

### [17] 0x3B67FC-0x3B6804

- **Size:** 8 bytes, 4 glyphs (2 kanji)
- **Decoded:** `  ちち`
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 00 00 00 80 00 80 00`

### [18] 0x3B6806-0x3B6816

- **Size:** 16 bytes, 8 glyphs (3 kanji)
- **Decoded:** `ちブブ  ( =`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `80 00 00 01 00 01 00 00 00 00 08 00 00 00 1d 00`

### [19] 0x3B6818-0x3B6820

- **Size:** 8 bytes, 4 glyphs (2 kanji)
- **Decoded:** `  ちち`
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 00 00 00 80 00 80 00`

### [20] 0x3B6822-0x3B6832

- **Size:** 16 bytes, 8 glyphs (3 kanji)
- **Decoded:** `ちブブ  ( :`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `80 00 00 01 00 01 00 00 00 00 08 00 00 00 1a 00`

### [21] 0x3B6836-0x3B683E

- **Size:** 8 bytes, 4 glyphs (2 kanji)
- **Decoded:** `rちち `
- **Purpose:** Short text (code/early-data)
- **Hex:** `52 00 80 00 80 00 00 00`

### [22] 0x3B6852-0x3B685A

- **Size:** 8 bytes, 4 glyphs (3 kanji)
- **Decoded:** `うちち `
- **Purpose:** Short text (code/early-data)
- **Hex:** `72 00 80 00 80 00 00 00`

### [23] 0x3B686C-0x3B6876

- **Size:** 10 bytes, 5 glyphs (3 kanji)
- **Decoded:** `\うちち `
- **Purpose:** Short text (code/early-data)
- **Hex:** `3c 00 72 00 80 00 80 00 00 00`

### [24] 0x3B6888-0x3B6892

- **Size:** 10 bytes, 5 glyphs (3 kanji)
- **Decoded:** `なrちち `
- **Purpose:** Short text (code/early-data)
- **Hex:** `84 00 52 00 80 00 80 00 00 00`

### [25] 0x3B68A6-0x3B68AE

- **Size:** 8 bytes, 4 glyphs (2 kanji)
- **Decoded:** `2ちち `
- **Purpose:** Short text (code/early-data)
- **Hex:** `12 00 80 00 80 00 00 00`

### [26] 0x3B68C0-0x3B68CA

- **Size:** 10 bytes, 5 glyphs (2 kanji)
- **Decoded:** `\2ちち `
- **Purpose:** Short text (code/early-data)
- **Hex:** `3c 00 12 00 80 00 80 00 00 00`

### [27] 0x3B693C-0x3B6948

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ  ( `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 08 00 00 00`

### [28] 0x3B6990-0x3B6998

- **Size:** 8 bytes, 4 glyphs (2 kanji)
- **Decoded:** `p@ぜぜ`
- **Purpose:** Short text (code/early-data)
- **Hex:** `50 00 20 00 a6 00 a6 00`

### [29] 0x3B6A00-0x3B6A08

- **Size:** 8 bytes, 4 glyphs (2 kanji)
- **Decoded:** `  ぜぜ`
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 00 00 00 a6 00 a6 00`

### [30] 0x3B6A0A-0x3B6A1A

- **Size:** 16 bytes, 8 glyphs (3 kanji)
- **Decoded:** `ちブブ  ( :`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `80 00 00 01 00 01 00 00 00 00 08 00 00 00 1a 00`

### [31] 0x3B6A1E-0x3B6A26

- **Size:** 8 bytes, 4 glyphs (2 kanji)
- **Decoded:** `Bぜぜ `
- **Purpose:** Short text (code/early-data)
- **Hex:** `22 00 a6 00 a6 00 00 00`

### [32] 0x3B6A38-0x3B6A42

- **Size:** 10 bytes, 5 glyphs (2 kanji)
- **Decoded:** `tBぜぜ `
- **Purpose:** Short text (code/early-data)
- **Hex:** `54 00 22 00 a6 00 a6 00 00 00`

### [33] 0x3B6A98-0x3B6AA4

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ  ( `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 08 00 00 00`

### [34] 0x3B6AE0-0x3B6AE8

- **Size:** 8 bytes, 4 glyphs (2 kanji)
- **Decoded:** `p@ぜぜ`
- **Purpose:** Short text (code/early-data)
- **Hex:** `50 00 20 00 a6 00 a6 00`

### [35] 0x3B6B50-0x3B6B58

- **Size:** 8 bytes, 4 glyphs (2 kanji)
- **Decoded:** `  ぜぜ`
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 00 00 00 a6 00 a6 00`

### [36] 0x3B6B5A-0x3B6B6A

- **Size:** 16 bytes, 8 glyphs (3 kanji)
- **Decoded:** `ちブブ  ( ;`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `80 00 00 01 00 01 00 00 00 00 08 00 00 00 1b 00`

### [37] 0x3B6B6E-0x3B6B76

- **Size:** 8 bytes, 4 glyphs (2 kanji)
- **Decoded:** `Bぜぜ `
- **Purpose:** Short text (code/early-data)
- **Hex:** `22 00 a6 00 a6 00 00 00`

### [38] 0x3B6B88-0x3B6B92

- **Size:** 10 bytes, 5 glyphs (2 kanji)
- **Decoded:** `tBぜぜ `
- **Purpose:** Short text (code/early-data)
- **Hex:** `54 00 22 00 a6 00 a6 00 00 00`

### [39] 0x3B6BE8-0x3B6BF4

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ  ( `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 08 00 00 00`

### [40] 0x3B6C20-0x3B6C38

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    %"る0初``
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 05 00 02 00 98 00 10 00 60 01 40 00`

### [41] 0x3B6C3C-0x3B6C48

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ  ( `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 08 00 00 00`

### [42] 0x3B6C80-0x3B6C98

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    %0(ち@ミ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 05 00 10 00 08 00 80 00 20 00 e0 00`

### [43] 0x3B6CF0-0x3B6D08

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    %' ちぐミ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 05 00 07 00 00 00 80 00 a0 00 e0 00`

### [44] 0x3B6D0C-0x3B6D18

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ  ( `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 08 00 00 00`

### [45] 0x3B6D50-0x3B6D68

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `別ブ    %-(ち@ミ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 02 00 01 00 00 00 00 00 00 00 00 05 00 0d 00 08 00 80 00 20 00 e0 00`

### [46] 0x3B6D88-0x3B6D94

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `別ブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 02 00 01 00 00 00 00 00 00 00 00`

### [47] 0x3B6DA4-0x3B6DBC

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    %*ッ あ0`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 05 00 0a 00 10 01 00 00 70 00 10 00`

### [48] 0x3B6DF8-0x3B6E04

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [49] 0x3B6E30-0x3B6E40

- **Size:** 16 bytes, 8 glyphs (3 kanji)
- **Decoded:** `ブブ    )の`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 09 00 88 00`

### [50] 0x3B6EA0-0x3B6EAC

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [51] 0x3B6FC0-0x3B6FCC

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [52] 0x3B70E0-0x3B70EC

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [53] 0x3B7120-0x3B7132

- **Size:** 18 bytes, 9 glyphs (3 kanji)
- **Decoded:** `ブブ    )のB`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 09 00 88 00 22 00`

### [54] 0x3B7190-0x3B71A8

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `"ブ  ( )のBし戦B`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `02 00 00 01 00 00 00 00 08 00 00 00 09 00 88 00 22 00 7b 00 1e 01 22 00`

### [55] 0x3B720C-0x3B7224

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    ([?99]bち  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 08 00 63 00 42 00 80 00 00 00 00 00`

### [56] 0x3B7228-0x3B7240

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    (♥(ち  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 08 00 5f 00 08 00 80 00 00 00 00 00`

### [57] 0x3B7244-0x3B725C

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    ([?100]びち  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 08 00 64 00 ae 00 80 00 00 00 00 00`

### [58] 0x3B7260-0x3B7278

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    (♥うち  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 08 00 5f 00 72 00 80 00 00 00 00 00`

### [59] 0x3B727C-0x3B7294

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    ([?101]騎ち  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 08 00 65 00 18 01 80 00 00 00 00 00`

### [60] 0x3B7298-0x3B72B0

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    ([?96]ホち  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 08 00 60 00 de 00 80 00 00 00 00 00`

### [61] 0x3B72B4-0x3B72CC

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    ([?102]bニ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 08 00 66 00 42 00 d6 00 00 00 00 00`

### [62] 0x3B72D0-0x3B72E8

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    (♥(ニ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 08 00 5f 00 08 00 d6 00 00 00 00 00`

### [63] 0x3B72EC-0x3B7304

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    ([?103]びニ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 08 00 67 00 ae 00 d6 00 00 00 00 00`

### [64] 0x3B7308-0x3B7320

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    (♥うニ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 08 00 5f 00 72 00 d6 00 00 00 00 00`

### [65] 0x3B7324-0x3B733C

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    ([?104]騎ニ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 08 00 68 00 18 01 d6 00 00 00 00 00`

### [66] 0x3B7340-0x3B7358

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    ([?96]ホニ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 08 00 60 00 de 00 d6 00 00 00 00 00`

### [67] 0x3B735C-0x3B7368

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [68] 0x3B73BC-0x3B73C8

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [69] 0x3B741C-0x3B7428

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [70] 0x3B7460-0x3B7478

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    (％h[?108]  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 08 00 6d 00 48 00 6c 00 00 00 00 00`

### [71] 0x3B747C-0x3B7494

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    (えp[?108]子(`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 08 00 73 00 50 00 6c 00 9e 01 08 00`

### [72] 0x3B7498-0x3B74B0

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  ( ([?108]帰[?108]  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 08 00 00 00 08 00 6c 00 ee 01 6c 00 00 00 00 00`

### [73] 0x3B74B4-0x3B74C0

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [74] 0x3B74F0-0x3B7508

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    (％h[?108]  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 08 00 6d 00 48 00 6c 00 00 00 00 00`

### [75] 0x3B750C-0x3B7524

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    (えp[?108]子(`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 08 00 73 00 50 00 6c 00 9e 01 08 00`

### [76] 0x3B7528-0x3B7540

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  ( ([?108]帰[?108]  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 08 00 00 00 08 00 6c 00 ee 01 6c 00 00 00 00 00`

### [77] 0x3B7544-0x3B7550

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [78] 0x3B7580-0x3B7598

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    (％h[?108]  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 08 00 6d 00 48 00 6c 00 00 00 00 00`

### [79] 0x3B759C-0x3B75B4

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    (えp[?108]子(`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 08 00 73 00 50 00 6c 00 9e 01 08 00`

### [80] 0x3B75B8-0x3B75D0

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  ( ([?108]帰[?108]  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 08 00 00 00 08 00 6c 00 ee 01 6c 00 00 00 00 00`

### [81] 0x3B75D4-0x3B75E0

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [82] 0x3B7610-0x3B7628

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    (％h[?108]  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 08 00 6d 00 48 00 6c 00 00 00 00 00`

### [83] 0x3B762C-0x3B7644

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    (えp[?108]子(`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 08 00 73 00 50 00 6c 00 9e 01 08 00`

### [84] 0x3B7648-0x3B7660

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  ( ([?108]帰[?108]  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 08 00 00 00 08 00 6c 00 ee 01 6c 00 00 00 00 00`

### [85] 0x3B7664-0x3B7670

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [86] 0x3B76A0-0x3B76B8

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    (％h[?108]  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 08 00 6d 00 48 00 6c 00 00 00 00 00`

### [87] 0x3B76BC-0x3B76D4

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    (えp[?108]子(`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 08 00 73 00 50 00 6c 00 9e 01 08 00`

### [88] 0x3B76D8-0x3B76F0

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  ( ([?108]帰[?108]  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 08 00 00 00 08 00 6c 00 ee 01 6c 00 00 00 00 00`

### [89] 0x3B76F4-0x3B7700

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [90] 0x3B7730-0x3B7748

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    (％h[?108]  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 08 00 6d 00 48 00 6c 00 00 00 00 00`

### [91] 0x3B774C-0x3B7764

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    (えp[?108]子(`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 08 00 73 00 50 00 6c 00 9e 01 08 00`

### [92] 0x3B7768-0x3B7780

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  ( ([?108]帰[?108]  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 08 00 00 00 08 00 6c 00 ee 01 6c 00 00 00 00 00`

### [93] 0x3B7784-0x3B7790

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [94] 0x3B77C0-0x3B77D8

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    ,ぎあH0べ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 0c 00 9f 00 70 00 28 00 10 00 b0 00`

### [95] 0x3B77F8-0x3B7810

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `"ブ  ( )ね0Hあぐ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `02 00 00 01 00 00 00 00 08 00 00 00 09 00 87 00 10 00 28 00 70 00 a0 00`

### [96] 0x3B7850-0x3B7868

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    ,ぎあH0べ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 0c 00 9f 00 70 00 28 00 10 00 b0 00`

### [97] 0x3B7888-0x3B78A0

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `"ブ  ( )ね0Hあぐ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `02 00 00 01 00 00 00 00 08 00 00 00 09 00 87 00 10 00 28 00 70 00 a0 00`

### [98] 0x3B78E0-0x3B78F8

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    %8込落  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 05 00 18 00 d8 01 98 01 00 00 00 00`

### [99] 0x3B78FC-0x3B7914

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    %:H落時@`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 05 00 1a 00 28 00 98 01 b0 01 20 00`

### [100] 0x3B7934-0x3B794C

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  ( %<込H@看`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 08 00 00 00 05 00 1c 00 d8 01 28 00 20 00 70 01`

### [101] 0x3B7950-0x3B795C

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ  ( `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 08 00 00 00`

### [102] 0x3B7990-0x3B79A8

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    ,ぎあN0べ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 0c 00 9f 00 70 00 2e 00 10 00 b0 00`

### [103] 0x3B79C8-0x3B79E0

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `"ブ  ( )ね0Nあぐ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `02 00 00 01 00 00 00 00 08 00 00 00 09 00 87 00 10 00 2e 00 70 00 a0 00`

### [104] 0x3B79E4-0x3B79FC

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `"ブ  ( )の祠^pど`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `02 00 00 01 00 00 00 00 08 00 00 00 09 00 88 00 12 01 3e 00 50 00 ac 00`

### [105] 0x3B7A1C-0x3B7A60

- **Size:** 68 bytes, 34 glyphs (12 kanji)
- **Decoded:** `ブブ        ふまへほみよるらりれ      2[1\3]4^`
- **Purpose:** Long text string (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 8b 00 8e 00 8c 00 8d`

### [106] 0x3B7B26-0x3B7B2E

- **Size:** 8 bytes, 4 glyphs (2 kanji)
- **Decoded:** `[?100]J(ご`
- **Purpose:** Short text (code/early-data)
- **Hex:** `64 00 2a 00 08 00 a2 00`

### [107] 0x3B7B4A-0x3B7B52

- **Size:** 8 bytes, 4 glyphs (2 kanji)
- **Decoded:** `[?102]D)ぐ`
- **Purpose:** Short text (code/early-data)
- **Hex:** `66 00 24 00 09 00 a0 00`

### [108] 0x3B7C32-0x3B7CD2

- **Size:** 160 bytes, 80 glyphs (38 kanji)
- **Decoded:** `wxyz{|}~♥[?96][?97][?98][?99][?100][?101][?102][?103][?104][?105][?106][?107][?108]％[?110][?111]あいうえお Eそ Fた"Gち!Hつ#Iて&Jと'Kな%Lに$Mぬ(Nね*Oの)Pは+Qひ,Rふ-Sへ.Tほ/B`
- **Purpose:** Long text string (code/early-data)
- **Hex:** `57 00 58 00 59 00 5a 00 5b 00 5c 00 5d 00 5e 00 5f 00 60 00 61 00 62 00 63 00 64`

### [109] 0x3B7D6C-0x3B7D78

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ  ( `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 08 00 00 00`

### [110] 0x3B7E58-0x3B7E64

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ  $ `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00`

### [111] 0x3B7E74-0x3B7E88

- **Size:** 20 bytes, 10 glyphs (3 kanji)
- **Decoded:** `ブブ    $$ぷH`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 04 00 b4 00 28 00`

### [112] 0x3B7EE8-0x3B7EF4

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [113] 0x3B7F20-0x3B7F2C

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [114] 0x3B81C8-0x3B81E0

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ !$[?96]0[?96]だ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 01 00 04 00 60 00 10 00 60 00 a8 00`

### [115] 0x3B8200-0x3B8218

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    !&0ゅpゅ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 01 00 06 00 10 00 b8 00 50 00 b8 00`

### [116] 0x3B821C-0x3B8234

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ !'[?96]ゅ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 01 00 07 00 60 00 b8 00 00 00 00 00`

### [117] 0x3B8254-0x3B8260

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [118] 0x3B8270-0x3B8288

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ      ,$[?96]ぉ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 00 00 00 00 0c 00 04 00 60 00 be 00`

### [119] 0x3B83B8-0x3B83C4

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ  $ `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00`

### [120] 0x3B83D4-0x3B83E8

- **Size:** 20 bytes, 10 glyphs (3 kanji)
- **Decoded:** `ブブ    $$ぷH`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 04 00 b4 00 28 00`

### [121] 0x3B85F0-0x3B85FC

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ  $ `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00`

### [122] 0x3B866C-0x3B8678

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [123] 0x3B86B0-0x3B86BC

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [124] 0x3B86CC-0x3B86E8

- **Size:** 28 bytes, 14 glyphs (5 kanji)
- **Decoded:** `ブブ        `[?96]二鎧`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 40 00 60 00 80 01 20`

### [125] 0x3B8764-0x3B877C

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    CT@ッ`ッ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 23 00 34 00 20 00 10 01 40 00 10 01`

### [126] 0x3B880C-0x3B8824

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    CZ@ッ`ッ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 23 00 3a 00 20 00 10 01 40 00 10 01`

### [127] 0x3B8828-0x3B8834

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ  $ `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00`

### [128] 0x3B8860-0x3B886C

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ !  `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 01 00 00 00 00 00`

### [129] 0x3B88A0-0x3B88AC

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ "  `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 02 00 00 00 00 00`

### [130] 0x3B88E0-0x3B88EC

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [131] 0x3B8974-0x3B898C

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<べ0べぐ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 b0 00 10 00 b0 00 a0 00`

### [132] 0x3B89AC-0x3B89C4

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    $>0べぐべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 a0 00 b0 00`

### [133] 0x3B89C8-0x3B89E0

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?べべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 b0 00 b0 00 00 00 00 00`

### [134] 0x3B89E4-0x3B89F0

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [135] 0x3B8A3C-0x3B8A54

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9す ぐ `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 7c 00 00 00 a0 00 00 00`

### [136] 0x3B8A90-0x3B8AA8

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<べ0べぐ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 b0 00 10 00 b0 00 a0 00`

### [137] 0x3B8AC8-0x3B8AE0

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    $>0べぐべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 a0 00 b0 00`

### [138] 0x3B8AE4-0x3B8AFC

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?べべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 b0 00 b0 00 00 00 00 00`

### [139] 0x3B8B1C-0x3B8B2E

- **Size:** 18 bytes, 9 glyphs (3 kanji)
- **Decoded:** `ブブ    $A[?100]`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 21 00 64 00`

### [140] 0x3B8B54-0x3B8B60

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ !  `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 01 00 00 00 00 00`

### [141] 0x3B8BE4-0x3B8BFC

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<べ0べぐ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 b0 00 10 00 b0 00 a0 00`

### [142] 0x3B8C1C-0x3B8C34

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $>0べTべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 34 00 b0 00`

### [143] 0x3B8C38-0x3B8C50

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>すべぐべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 7c 00 b0 00 a0 00 b0 00`

### [144] 0x3B8C54-0x3B8C6C

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?べべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 b0 00 b0 00 00 00 00 00`

### [145] 0x3B8C8C-0x3B8CA4

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $C[?100]べ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 23 00 64 00 b0 00 00 00 00 00`

### [146] 0x3B8CC4-0x3B8CD0

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ "  `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 02 00 00 00 00 00`

### [147] 0x3B8D1C-0x3B8D34

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9す ぐ `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 7c 00 00 00 a0 00 00 00`

### [148] 0x3B8D70-0x3B8D88

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<べ0べぐ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 b0 00 10 00 b0 00 a0 00`

### [149] 0x3B8DA8-0x3B8DC0

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $>0べTべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 34 00 b0 00`

### [150] 0x3B8DC4-0x3B8DDC

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>すべぐべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 7c 00 b0 00 a0 00 b0 00`

### [151] 0x3B8DE0-0x3B8DF8

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?べべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 b0 00 b0 00 00 00 00 00`

### [152] 0x3B8E18-0x3B8E2A

- **Size:** 18 bytes, 9 glyphs (3 kanji)
- **Decoded:** `ブブ    $A[?100]`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 21 00 64 00`

### [153] 0x3B8E50-0x3B8E68

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $C[?100]べ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 23 00 64 00 b0 00 00 00 00 00`

### [154] 0x3B8EA4-0x3B8EB0

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ "  `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 02 00 00 00 00 00`

### [155] 0x3B8EC0-0x3B8ED8

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ      %%ゅぽ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 00 00 00 00 05 00 05 00 b8 00 b6 00`

### [156] 0x3B8F00-0x3B8F0C

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ #  `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 03 00 00 00 00 00`

### [157] 0x3B8F40-0x3B8F4C

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ $  `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 04 00 00 00 00 00`

### [158] 0x3B8FD4-0x3B8FEC

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<ミ0ミぐ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 e0 00 10 00 e0 00 a0 00`

### [159] 0x3B900C-0x3B9024

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    $>0べタべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 d0 00 b0 00`

### [160] 0x3B9028-0x3B9040

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?ミべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 e0 00 b0 00 00 00 00 00`

### [161] 0x3B9044-0x3B9050

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [162] 0x3B909C-0x3B90B4

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9ゆ タ `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 94 00 00 00 d0 00 00 00`

### [163] 0x3B90F0-0x3B9108

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<ミ0ミぐ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 e0 00 10 00 e0 00 a0 00`

### [164] 0x3B9128-0x3B9140

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    $>0べタべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 d0 00 b0 00`

### [165] 0x3B9144-0x3B915C

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?ミべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 e0 00 b0 00 00 00 00 00`

### [166] 0x3B917C-0x3B918E

- **Size:** 18 bytes, 9 glyphs (3 kanji)
- **Decoded:** `ブブ    $Aす`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 21 00 7c 00`

### [167] 0x3B9198-0x3B91AA

- **Size:** 18 bytes, 9 glyphs (3 kanji)
- **Decoded:** `ブブ    $e[?108]`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 45 00 6c 00`

### [168] 0x3B91B4-0x3B91C0

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ !  `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 01 00 00 00 00 00`

### [169] 0x3B9244-0x3B925C

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<ミ0ミぐ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 e0 00 10 00 e0 00 a0 00`

### [170] 0x3B927C-0x3B9294

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $>0べlべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 4c 00 b0 00`

### [171] 0x3B9298-0x3B92B0

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>ゆべタべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 94 00 b0 00 d0 00 b0 00`

### [172] 0x3B92B4-0x3B92CC

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?ミべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 e0 00 b0 00 00 00 00 00`

### [173] 0x3B92EC-0x3B9304

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $Cすべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 23 00 7c 00 b0 00 00 00 00 00`

### [174] 0x3B9308-0x3B9320

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $h[?108]ぷ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 48 00 6c 00 b4 00 00 00 00 00`

### [175] 0x3B9324-0x3B9330

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ "  `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 02 00 00 00 00 00`

### [176] 0x3B937C-0x3B9394

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9ゆ タ `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 94 00 00 00 d0 00 00 00`

### [177] 0x3B93D0-0x3B93E8

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<ミ0ミぐ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 e0 00 10 00 e0 00 a0 00`

### [178] 0x3B9408-0x3B9420

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $>0べlべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 4c 00 b0 00`

### [179] 0x3B9424-0x3B943C

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>ゆべタべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 94 00 b0 00 d0 00 b0 00`

### [180] 0x3B9440-0x3B9458

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?ミべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 e0 00 b0 00 00 00 00 00`

### [181] 0x3B9478-0x3B948A

- **Size:** 18 bytes, 9 glyphs (3 kanji)
- **Decoded:** `ブブ    $Aす`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 21 00 7c 00`

### [182] 0x3B94B0-0x3B94C8

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $Cすべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 23 00 7c 00 b0 00 00 00 00 00`

### [183] 0x3B94CC-0x3B94DE

- **Size:** 18 bytes, 9 glyphs (3 kanji)
- **Decoded:** `ブブ    $e[?108]`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 45 00 6c 00`

### [184] 0x3B94E8-0x3B9500

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ !  $h[?108]ぷ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 01 00 00 00 00 00 04 00 48 00 6c 00 b4 00 00 00 00 00`

### [185] 0x3B9504-0x3B9510

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ "  `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 02 00 00 00 00 00`

### [186] 0x3B9520-0x3B9538

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ      $$ヨぷ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 00 00 00 00 04 00 04 00 e6 00 b4 00`

### [187] 0x3B95EC-0x3B95F8

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [188] 0x3B9768-0x3B9774

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ  $ `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00`

### [189] 0x3B9784-0x3B9798

- **Size:** 20 bytes, 10 glyphs (3 kanji)
- **Decoded:** `ブブ    $$フt`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 04 00 dc 00 54 00`

### [190] 0x3B9814-0x3B982C

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $$込0込[?100]`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 04 00 d8 01 10 00 d8 01 64 00`

### [191] 0x3B9830-0x3B983C

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ  $ `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00`

### [192] 0x3B98A0-0x3B98B8

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $Eけべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 25 00 78 00 b0 00 00 00 00 00`

### [193] 0x3B98F4-0x3B990C

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9の ぐ `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 88 00 00 00 a0 00 00 00`

### [194] 0x3B9948-0x3B9960

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<べ0べぐ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 b0 00 10 00 b0 00 a0 00`

### [195] 0x3B9980-0x3B9998

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    $>0べけべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 78 00 b0 00`

### [196] 0x3B999C-0x3B99B4

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>のべぐべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 88 00 b0 00 a0 00 b0 00`

### [197] 0x3B99B8-0x3B99D0

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?べべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 b0 00 b0 00 00 00 00 00`

### [198] 0x3B99D4-0x3B99E0

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [199] 0x3B9A10-0x3B9A28

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $Eけべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 25 00 78 00 b0 00 00 00 00 00`

### [200] 0x3B9A80-0x3B9A98

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $9の ぐ `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 19 00 88 00 00 00 a0 00 00 00`

### [201] 0x3B9AD4-0x3B9AEC

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<べ0べぐ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 b0 00 10 00 b0 00 a0 00`

### [202] 0x3B9B0C-0x3B9B24

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    $>0べけべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 78 00 b0 00`

### [203] 0x3B9B28-0x3B9B40

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>のべぐべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 88 00 b0 00 a0 00 b0 00`

### [204] 0x3B9B44-0x3B9B5C

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?べべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 b0 00 b0 00 00 00 00 00`

### [205] 0x3B9BB4-0x3B9BC0

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ !  `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 01 00 00 00 00 00`

### [206] 0x3B9BF0-0x3B9C08

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $Eけべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 25 00 78 00 b0 00 00 00 00 00`

### [207] 0x3B9C44-0x3B9C5C

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9の ぐ `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 88 00 00 00 a0 00 00 00`

### [208] 0x3B9C98-0x3B9CB0

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<べ0べぐ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 b0 00 10 00 b0 00 a0 00`

### [209] 0x3B9CD0-0x3B9CE8

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $>0べ8べ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 18 00 b0 00`

### [210] 0x3B9CEC-0x3B9D04

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $>[?104]べ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 68 00 b0 00 00 00 00 00`

### [211] 0x3B9D08-0x3B9D20

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ    $>のべぐべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 88 00 b0 00 a0 00 b0 00`

### [212] 0x3B9D24-0x3B9D3C

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?べべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 b0 00 b0 00 00 00 00 00`

### [213] 0x3B9D94-0x3B9DA0

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ "  `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 02 00 00 00 00 00`

### [214] 0x3B9DD0-0x3B9DE8

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $Eけべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 25 00 78 00 b0 00 00 00 00 00`

### [215] 0x3B9E40-0x3B9E58

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $9の ぐ `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 19 00 88 00 00 00 a0 00 00 00`

### [216] 0x3B9E94-0x3B9EAC

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<べ0べぐ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 b0 00 10 00 b0 00 a0 00`

### [217] 0x3B9ECC-0x3B9EE4

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $>0べ8べ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 18 00 b0 00`

### [218] 0x3B9EE8-0x3B9F00

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $>[?104]べ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 68 00 b0 00 00 00 00 00`

### [219] 0x3B9F04-0x3B9F1C

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ    $>のべぐべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 88 00 b0 00 a0 00 b0 00`

### [220] 0x3B9F20-0x3B9F38

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?べべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 b0 00 b0 00 00 00 00 00`

### [221] 0x3B9FE4-0x3B9FF0

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ "  `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 02 00 00 00 00 00`

### [222] 0x3BA000-0x3BA018

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ      $$ゅぷ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 00 00 00 00 04 00 04 00 b8 00 b4 00`

### [223] 0x3BA05C-0x3BA074

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $Eけべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 25 00 78 00 b0 00 00 00 00 00`

### [224] 0x3BA078-0x3BA090

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $E腕べ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 25 00 38 01 b0 00 00 00 00 00`

### [225] 0x3BA0CC-0x3BA0E4

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9の 王 `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 88 00 00 00 28 01 00 00`

### [226] 0x3BA0E8-0x3BA100

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9上 初 `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 48 01 00 00 60 01 00 00`

### [227] 0x3BA13C-0x3BA154

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<看0看ぐ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 70 01 10 00 70 01 a0 00`

### [228] 0x3BA174-0x3BA18C

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    $>0べけべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 78 00 b0 00`

### [229] 0x3BA190-0x3BA1A8

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>のべ王べ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 88 00 b0 00 28 01 b0 00`

### [230] 0x3BA1AC-0x3BA1C4

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>上べ多べ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 48 01 b0 00 64 01 b0 00`

### [231] 0x3BA1C8-0x3BA1E0

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?看べ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 70 01 b0 00 00 00 00 00`

### [232] 0x3BA1E4-0x3BA1F0

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [233] 0x3BA23C-0x3BA254

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $Eけべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 25 00 78 00 b0 00 00 00 00 00`

### [234] 0x3BA258-0x3BA270

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $E腕べ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 25 00 38 01 b0 00 00 00 00 00`

### [235] 0x3BA2AC-0x3BA2C4

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9の る `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 88 00 00 00 98 00 00 00`

### [236] 0x3BA2C8-0x3BA2E0

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9ミ 王 `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 e0 00 00 00 28 01 00 00`

### [237] 0x3BA2E4-0x3BA2FC

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9上 初 `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 48 01 00 00 60 01 00 00`

### [238] 0x3BA338-0x3BA350

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<看0看ぐ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 70 01 10 00 70 01 a0 00`

### [239] 0x3BA370-0x3BA388

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    $>0べけべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 78 00 b0 00`

### [240] 0x3BA38C-0x3BA3A4

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>のべ王べ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 88 00 b0 00 28 01 b0 00`

### [241] 0x3BA3A8-0x3BA3C0

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>上べ初べ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 48 01 b0 00 60 01 b0 00`

### [242] 0x3BA3C4-0x3BA3DC

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?看べ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 70 01 b0 00 00 00 00 00`

### [243] 0x3BA3E0-0x3BA3F2

- **Size:** 18 bytes, 9 glyphs (3 kanji)
- **Decoded:** `ブブ    $@だ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 20 00 a8 00`

### [244] 0x3BA3FC-0x3BA40E

- **Size:** 18 bytes, 9 glyphs (3 kanji)
- **Decoded:** `ブブ    $Aク`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 21 00 c8 00`

### [245] 0x3BA418-0x3BA42A

- **Size:** 18 bytes, 9 glyphs (3 kanji)
- **Decoded:** `ブブ    $eゅ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 45 00 b8 00`

### [246] 0x3BA434-0x3BA440

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ !  `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 01 00 00 00 00 00`

### [247] 0x3BA48C-0x3BA4A4

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $Eけべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 25 00 78 00 b0 00 00 00 00 00`

### [248] 0x3BA4A8-0x3BA4C0

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $E腕べ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 25 00 38 01 b0 00 00 00 00 00`

### [249] 0x3BA4FC-0x3BA514

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9の 王 `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 88 00 00 00 28 01 00 00`

### [250] 0x3BA518-0x3BA530

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9上 初 `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 48 01 00 00 60 01 00 00`

### [251] 0x3BA56C-0x3BA584

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<看0看ぐ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 70 01 10 00 70 01 a0 00`

### [252] 0x3BA5A4-0x3BA5BC

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    $>0べけべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 78 00 b0 00`

### [253] 0x3BA5C0-0x3BA5D8

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>のべるべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 88 00 b0 00 98 00 b0 00`

### [254] 0x3BA5DC-0x3BA5F4

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>ミべ王べ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 e0 00 b0 00 28 01 b0 00`

### [255] 0x3BA5F8-0x3BA610

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>上べ初べ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 48 01 b0 00 60 01 b0 00`

### [256] 0x3BA614-0x3BA62C

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?看べ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 70 01 b0 00 00 00 00 00`

### [257] 0x3BA630-0x3BA648

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $Bだべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 22 00 a8 00 b0 00 00 00 00 00`

### [258] 0x3BA64C-0x3BA664

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $Cクべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 23 00 c8 00 b0 00 00 00 00 00`

### [259] 0x3BA668-0x3BA680

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $hゅぷ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 48 00 b8 00 b4 00 00 00 00 00`

### [260] 0x3BA684-0x3BA690

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ "  `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 02 00 00 00 00 00`

### [261] 0x3BA6DC-0x3BA6F4

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $Eけべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 25 00 78 00 b0 00 00 00 00 00`

### [262] 0x3BA6F8-0x3BA710

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $E腕べ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 25 00 38 01 b0 00 00 00 00 00`

### [263] 0x3BA74C-0x3BA764

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9の る `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 88 00 00 00 98 00 00 00`

### [264] 0x3BA768-0x3BA780

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9ミ 王 `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 e0 00 00 00 28 01 00 00`

### [265] 0x3BA784-0x3BA79C

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9上 初 `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 48 01 00 00 60 01 00 00`

### [266] 0x3BA7D8-0x3BA7F0

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<看0看ぐ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 70 01 10 00 70 01 a0 00`

### [267] 0x3BA810-0x3BA828

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    $>0べけべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 78 00 b0 00`

### [268] 0x3BA82C-0x3BA844

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>のべるべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 88 00 b0 00 98 00 b0 00`

### [269] 0x3BA848-0x3BA860

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>ミべ王べ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 e0 00 b0 00 28 01 b0 00`

### [270] 0x3BA864-0x3BA87C

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>上べ初べ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 48 01 b0 00 60 01 b0 00`

### [271] 0x3BA880-0x3BA898

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?看べ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 70 01 b0 00 00 00 00 00`

### [272] 0x3BA89C-0x3BA8AE

- **Size:** 18 bytes, 9 glyphs (3 kanji)
- **Decoded:** `ブブ    $@だ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 20 00 a8 00`

### [273] 0x3BA8B8-0x3BA8CA

- **Size:** 18 bytes, 9 glyphs (3 kanji)
- **Decoded:** `ブブ    $Aク`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 21 00 c8 00`

### [274] 0x3BA8D4-0x3BA8EC

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $Bだべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 22 00 a8 00 b0 00 00 00 00 00`

### [275] 0x3BA8F0-0x3BA908

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $Cクべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 23 00 c8 00 b0 00 00 00 00 00`

### [276] 0x3BA90C-0x3BA91E

- **Size:** 18 bytes, 9 glyphs (3 kanji)
- **Decoded:** `ブブ    $eゅ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 45 00 b8 00`

### [277] 0x3BA928-0x3BA940

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ !  $hゅぷ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 01 00 00 00 00 00 04 00 48 00 b8 00 b4 00 00 00 00 00`

### [278] 0x3BA944-0x3BA950

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ "  `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 02 00 00 00 00 00`

### [279] 0x3BA960-0x3BA978

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ      $$鉄ぷ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 00 00 00 00 04 00 04 00 78 01 b4 00`

### [280] 0x3BA9A0-0x3BA9B8

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $Eだべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 25 00 a8 00 b0 00 00 00 00 00`

### [281] 0x3BA9F4-0x3BAA0C

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9ゅ タ `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 b8 00 00 00 d0 00 00 00`

### [282] 0x3BAA48-0x3BAA60

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<ミ0ミぐ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 e0 00 10 00 e0 00 a0 00`

### [283] 0x3BAA80-0x3BAA98

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    $>0べるべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 98 00 b0 00`

### [284] 0x3BAA9C-0x3BAAB4

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>ゅべタべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 b8 00 b0 00 d0 00 b0 00`

### [285] 0x3BAAB8-0x3BAAD0

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?ミべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 e0 00 b0 00 00 00 00 00`

### [286] 0x3BAAD4-0x3BAAE0

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [287] 0x3BAB10-0x3BAB28

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $Eだべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 25 00 a8 00 b0 00 00 00 00 00`

### [288] 0x3BAB64-0x3BAB7C

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9す る `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 7c 00 00 00 98 00 00 00`

### [289] 0x3BAB80-0x3BAB98

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9ゅ タ `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 b8 00 00 00 d0 00 00 00`

### [290] 0x3BABD4-0x3BABEC

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<ミ0ミぐ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 e0 00 10 00 e0 00 a0 00`

### [291] 0x3BAC0C-0x3BAC24

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    $>0べるべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 98 00 b0 00`

### [292] 0x3BAC28-0x3BAC40

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>ゅべタべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 b8 00 b0 00 d0 00 b0 00`

### [293] 0x3BAC44-0x3BAC5C

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?ミべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 e0 00 b0 00 00 00 00 00`

### [294] 0x3BAC7C-0x3BAC8E

- **Size:** 18 bytes, 9 glyphs (3 kanji)
- **Decoded:** `ブブ    $A[?100]`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 21 00 64 00`

### [295] 0x3BACB4-0x3BACC0

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ !  `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 01 00 00 00 00 00`

### [296] 0x3BACF0-0x3BAD08

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $Eだべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 25 00 a8 00 b0 00 00 00 00 00`

### [297] 0x3BAD44-0x3BAD5C

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9ゅ タ `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 b8 00 00 00 d0 00 00 00`

### [298] 0x3BAD98-0x3BADB0

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<ミ0ミぐ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 e0 00 10 00 e0 00 a0 00`

### [299] 0x3BADD0-0x3BADE8

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $>0べTべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 34 00 b0 00`

### [300] 0x3BADEC-0x3BAE04

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>すべるべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 7c 00 b0 00 98 00 b0 00`

### [301] 0x3BAE08-0x3BAE20

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>ゅべタべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 b8 00 b0 00 d0 00 b0 00`

### [302] 0x3BAE24-0x3BAE3C

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?ミべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 e0 00 b0 00 00 00 00 00`

### [303] 0x3BAE5C-0x3BAE74

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $C[?100]べ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 23 00 64 00 b0 00 00 00 00 00`

### [304] 0x3BAE94-0x3BAEA0

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ "  `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 02 00 00 00 00 00`

### [305] 0x3BAED0-0x3BAEE8

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $Eだべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 25 00 a8 00 b0 00 00 00 00 00`

### [306] 0x3BAF24-0x3BAF3C

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9す る `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 7c 00 00 00 98 00 00 00`

### [307] 0x3BAF40-0x3BAF58

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9ゅ タ `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 b8 00 00 00 d0 00 00 00`

### [308] 0x3BAF94-0x3BAFAC

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<ミ0ミぐ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 e0 00 10 00 e0 00 a0 00`

### [309] 0x3BAFCC-0x3BAFE4

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $>0べTべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 34 00 b0 00`

### [310] 0x3BAFE8-0x3BB000

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>すべるべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 7c 00 b0 00 98 00 b0 00`

### [311] 0x3BB004-0x3BB01C

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>ゅべタべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 b8 00 b0 00 d0 00 b0 00`

### [312] 0x3BB020-0x3BB038

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?ミべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 e0 00 b0 00 00 00 00 00`

### [313] 0x3BB058-0x3BB06A

- **Size:** 18 bytes, 9 glyphs (3 kanji)
- **Decoded:** `ブブ    $A[?100]`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 21 00 64 00`

### [314] 0x3BB090-0x3BB0A8

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $C[?100]べ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 23 00 64 00 b0 00 00 00 00 00`

### [315] 0x3BB0E4-0x3BB0F0

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ "  `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 02 00 00 00 00 00`

### [316] 0x3BB100-0x3BB118

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ      $$ヨぷ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 00 00 00 00 04 00 04 00 e6 00 b4 00`

### [317] 0x3BB178-0x3BB184

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [318] 0x3BB194-0x3BB1A8

- **Size:** 20 bytes, 10 glyphs (3 kanji)
- **Decoded:** `ブブ    $$べT`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 04 00 b0 00 34 00`

### [319] 0x3BB358-0x3BB370

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    0ウ[?98]   `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 10 00 c3 00 62 00 00 00 00 00 00 00`

### [320] 0x3BB390-0x3BB39C

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [321] 0x3BB3F0-0x3BB3FC

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ %  `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 05 00 00 00 00 00`

### [322] 0x3BB430-0x3BB43C

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ #  `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 03 00 00 00 00 00`

### [323] 0x3BB470-0x3BB47C

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ $  `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 04 00 00 00 00 00`

### [324] 0x3BB61C-0x3BB628

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ  $ `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00`

### [325] 0x3BB70C-0x3BB718

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [326] 0x3BB750-0x3BB75C

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [327] 0x3BB8A8-0x3BB8B4

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ  $ `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00`

### [328] 0x3BB8C4-0x3BB8D8

- **Size:** 20 bytes, 10 glyphs (3 kanji)
- **Decoded:** `ブブ    $$フt`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 04 00 dc 00 54 00`

### [329] 0x3BB900-0x3BB918

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $Eだべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 25 00 a8 00 b0 00 00 00 00 00`

### [330] 0x3BB954-0x3BB96C

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9ゅ タ `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 b8 00 00 00 d0 00 00 00`

### [331] 0x3BB9A8-0x3BB9C0

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<ミ0ミぐ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 e0 00 10 00 e0 00 a0 00`

### [332] 0x3BB9E0-0x3BB9F8

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    $>0べるべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 98 00 b0 00`

### [333] 0x3BB9FC-0x3BBA14

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>ゅべタべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 b8 00 b0 00 d0 00 b0 00`

### [334] 0x3BBA18-0x3BBA30

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?ミべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 e0 00 b0 00 00 00 00 00`

### [335] 0x3BBA34-0x3BBA40

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [336] 0x3BBA50-0x3BBA68

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ      $$ヨぷ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 00 00 00 00 04 00 04 00 e6 00 b4 00`

### [337] 0x3BBBFC-0x3BBC14

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    $>0ちタち`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 80 00 d0 00 80 00`

### [338] 0x3BBC18-0x3BBC24

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ  $ `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00`

### [339] 0x3BBC34-0x3BBC48

- **Size:** 20 bytes, 10 glyphs (4 kanji)
- **Decoded:** `ブブ    $$フな`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 04 00 dc 00 84 00`

### [340] 0x3BBCFC-0x3BBD08

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [341] 0x3BBDB4-0x3BBDC0

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [342] 0x3BBE98-0x3BBEA4

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ  $ `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00`

### [343] 0x3BBEB4-0x3BBEC8

- **Size:** 20 bytes, 10 glyphs (3 kanji)
- **Decoded:** `ブブ    $$ぷH`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 04 00 b4 00 28 00`

### [344] 0x3BBF0C-0x3BBF24

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9べ エ `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 b0 00 00 00 c4 00 00 00`

### [345] 0x3BBF60-0x3BBF78

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<ト0トぐ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 d4 00 10 00 d4 00 a0 00`

### [346] 0x3BBF98-0x3BBFB0

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    $>0べむべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 90 00 b0 00`

### [347] 0x3BBFB4-0x3BBFCC

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>べべエべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 b0 00 b0 00 c4 00 b0 00`

### [348] 0x3BBFD0-0x3BBFE8

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?トべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 d4 00 b0 00 00 00 00 00`

### [349] 0x3BC008-0x3BC020

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $Eぐべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 25 00 a0 00 b0 00 00 00 00 00`

### [350] 0x3BC024-0x3BC030

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [351] 0x3BC07C-0x3BC094

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9お む `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 74 00 00 00 90 00 00 00`

### [352] 0x3BC098-0x3BC0B0

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9べ エ `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 b0 00 00 00 c4 00 00 00`

### [353] 0x3BC0EC-0x3BC104

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<ト0トぐ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 d4 00 10 00 d4 00 a0 00`

### [354] 0x3BC124-0x3BC13C

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    $>0べむべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 90 00 b0 00`

### [355] 0x3BC140-0x3BC158

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>べべエべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 b0 00 b0 00 c4 00 b0 00`

### [356] 0x3BC15C-0x3BC174

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?トべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 d4 00 b0 00 00 00 00 00`

### [357] 0x3BC1CC-0x3BC1E4

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $Eぐべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 25 00 a0 00 b0 00 00 00 00 00`

### [358] 0x3BC204-0x3BC210

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ !  `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 01 00 00 00 00 00`

### [359] 0x3BC25C-0x3BC274

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9べ エ `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 b0 00 00 00 c4 00 00 00`

### [360] 0x3BC2B0-0x3BC2C8

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<ト0トぐ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 d4 00 10 00 d4 00 a0 00`

### [361] 0x3BC2E8-0x3BC300

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $>0べLべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 2c 00 b0 00`

### [362] 0x3BC304-0x3BC31C

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>おべむべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 74 00 b0 00 90 00 b0 00`

### [363] 0x3BC320-0x3BC338

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>べべエべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 b0 00 b0 00 c4 00 b0 00`

### [364] 0x3BC33C-0x3BC354

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?トべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 d4 00 b0 00 00 00 00 00`

### [365] 0x3BC3AC-0x3BC3C4

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $Eぐべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 25 00 a0 00 b0 00 00 00 00 00`

### [366] 0x3BC3E4-0x3BC3F0

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ "  `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 02 00 00 00 00 00`

### [367] 0x3BC43C-0x3BC454

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9お む `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 74 00 00 00 90 00 00 00`

### [368] 0x3BC458-0x3BC470

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9べ エ `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 b0 00 00 00 c4 00 00 00`

### [369] 0x3BC4AC-0x3BC4C4

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<ト0トぐ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 d4 00 10 00 d4 00 a0 00`

### [370] 0x3BC4E4-0x3BC4FC

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $>0べLべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 2c 00 b0 00`

### [371] 0x3BC500-0x3BC518

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>おべむべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 74 00 b0 00 90 00 b0 00`

### [372] 0x3BC51C-0x3BC534

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>べべエべ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 b0 00 b0 00 c4 00 b0 00`

### [373] 0x3BC538-0x3BC550

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?トべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 d4 00 b0 00 00 00 00 00`

### [374] 0x3BC5E0-0x3BC5F8

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $Eぐべ  `
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 25 00 a0 00 b0 00 00 00 00 00`

### [375] 0x3BC634-0x3BC640

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ "  `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 02 00 00 00 00 00`

### [376] 0x3BC650-0x3BC668

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ      %%ハゃ`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 00 00 00 00 05 00 05 00 da 00 b7 00`

### [377] 0x3BC738-0x3BC744

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ  $ `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00`

### [378] 0x3BC754-0x3BC768

- **Size:** 20 bytes, 10 glyphs (3 kanji)
- **Decoded:** `ブブ    $$ぷG`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 04 00 b4 00 27 00`

### [379] 0x3BC7A2-0x3BC7AC

- **Size:** 10 bytes, 5 glyphs (2 kanji)
- **Decoded:** ` ざc[?98] `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 00 a3 00 43 00 62 00 00 00`

### [380] 0x3BC7B2-0x3BC7BC

- **Size:** 10 bytes, 5 glyphs (2 kanji)
- **Decoded:** ` じd[?98] `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 00 a4 00 44 00 62 00 00 00`

### [381] 0x3BC7C2-0x3BC7CC

- **Size:** 10 bytes, 5 glyphs (2 kanji)
- **Decoded:** ` ずe[?98] `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 00 a5 00 45 00 62 00 00 00`

### [382] 0x3BC7D2-0x3BC7DC

- **Size:** 10 bytes, 5 glyphs (2 kanji)
- **Decoded:** ` ぜf[?98] `
- **Purpose:** Short text (code/early-data)
- **Hex:** `00 00 a6 00 46 00 62 00 00 00`

### [383] 0x3BC7E4-0x3BC7F0

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `♥V[?99]   `
- **Purpose:** Short text (code/early-data)
- **Hex:** `5f 00 36 00 63 00 00 00 00 00 00 00`

### [384] 0x3BC856-0x3BC860

- **Size:** 10 bytes, 5 glyphs (2 kanji)
- **Decoded:** `][?96] ち `
- **Purpose:** Short text (code/early-data)
- **Hex:** `3d 00 60 00 00 00 80 00 00 00`

### [385] 0x3BC866-0x3BC870

- **Size:** 10 bytes, 5 glyphs (2 kanji)
- **Decoded:** `^[?96] ブ `
- **Purpose:** Short text (code/early-data)
- **Hex:** `3e 00 60 00 00 00 00 01 00 00`

### [386] 0x3BC876-0x3BC880

- **Size:** 10 bytes, 5 glyphs (2 kanji)
- **Decoded:** `_[?96] 別 `
- **Purpose:** Short text (code/early-data)
- **Hex:** `3f 00 60 00 00 00 00 02 00 00`

### [387] 0x3BC928-0x3BC950

- **Size:** 40 bytes, 20 glyphs (10 kanji)
- **Decoded:** `R   テトナニヌネノハヒフ      `
- **Purpose:** Long text string (code/early-data)
- **Hex:** `32 00 00 00 00 00 00 00 d3 00 d4 00 d5 00 d6 00 d7 00 d8 00 d9 00 da 00 db 00 dc`

### [388] 0x3BCA08-0x3BCA10

- **Size:** 8 bytes, 4 glyphs (2 kanji)
- **Decoded:** `ぼち  `
- **Purpose:** Short text (code/early-data)
- **Hex:** `b1 00 80 00 00 00 00 00`

### [389] 0x3BCA18-0x3BCA20

- **Size:** 8 bytes, 4 glyphs (2 kanji)
- **Decoded:** `ぱブ  `
- **Purpose:** Short text (code/early-data)
- **Hex:** `b2 00 00 01 00 00 00 00`

### [390] 0x3BCA28-0x3BCA30

- **Size:** 8 bytes, 4 glyphs (2 kanji)
- **Decoded:** `ぴ別  `
- **Purpose:** Short text (code/early-data)
- **Hex:** `b3 00 00 02 00 00 00 00`

### [391] 0x3BD6E8-0x3BD6F8

- **Size:** 16 bytes, 8 glyphs (3 kanji)
- **Decoded:** `    !ボ属呪`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 00 00 00 00 00 00 00 01 00 02 01 03 02 04 03`

### [392] 0x3BD738-0x3BD748

- **Size:** 16 bytes, 8 glyphs (3 kanji)
- **Decoded:** `    !ボ属呪`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 00 00 00 00 00 00 00 01 00 02 01 03 02 04 03`

### [393] 0x3BD788-0x3BD798

- **Size:** 16 bytes, 8 glyphs (3 kanji)
- **Decoded:** `    !ボ属呪`
- **Purpose:** Medium text (code/early-data)
- **Hex:** `00 00 00 00 00 00 00 00 01 00 02 01 03 02 04 03`

### [394] 0x3BF11A-0x3BF122

- **Size:** 8 bytes, 4 glyphs (3 kanji)
- **Decoded:** `期避p％`
- **Purpose:** Short text (code/early-data)
- **Hex:** `af 02 d5 02 50 00 6d 00`

### [395] 0x3BF140-0x3BF14E

- **Size:** 14 bytes, 7 glyphs (3 kanji)
- **Decoded:** `名J] も'別`
- **Purpose:** Short text (code/early-data)
- **Hex:** `c9 02 2a 00 3d 00 00 00 92 00 07 00 00 02`

### [396] 0x3BF190-0x3BF198

- **Size:** 8 bytes, 4 glyphs (4 kanji)
- **Decoded:** `備突難経`
- **Purpose:** Short text (code/early-data)
- **Hex:** `5a 02 78 02 02 03 0b 03`

### [397] 0x3BF1B4-0x3BF1BC

- **Size:** 8 bytes, 4 glyphs (3 kanji)
- **Decoded:** `異現"答`
- **Purpose:** Short text (code/early-data)
- **Hex:** `a6 02 e0 02 02 00 ec 02`

### [398] 0x3BF244-0x3BF24C

- **Size:** 8 bytes, 4 glyphs (3 kanji)
- **Decoded:** `噂兵"冒`
- **Purpose:** Short text (code/early-data)
- **Hex:** `dd 01 f3 01 02 00 da 02`

### [399] 0x3C055A-0x3C0566

- **Size:** 12 bytes, 6 glyphs (3 kanji)
- **Decoded:** `性難  %ブ`
- **Purpose:** Short text (pre-menu-data)
- **Hex:** `ff 01 02 03 00 00 00 00 05 00 00 01`

### [400] 0x3C056E-0x3C057A

- **Size:** 12 bytes, 6 glyphs (4 kanji)
- **Decoded:** `性難 $ブ難`
- **Purpose:** Short text (pre-menu-data)
- **Hex:** `ff 01 02 03 00 00 04 00 00 01 02 03`

### [401] 0x3C0590-0x3C059E

- **Size:** 14 bytes, 7 glyphs (3 kanji)
- **Decoded:** `種#  $ブ難`
- **Purpose:** Short text (pre-menu-data)
- **Hex:** `01 02 03 00 00 00 00 00 04 00 00 01 02 03`

### [402] 0x3C05A4-0x3C05B0

- **Size:** 12 bytes, 6 glyphs (3 kanji)
- **Decoded:** `種# #ブ難`
- **Purpose:** Short text (pre-menu-data)
- **Hex:** `01 02 03 00 00 00 03 00 00 01 02 03`

### [403] 0x3C05B4-0x3C05C2

- **Size:** 14 bytes, 7 glyphs (4 kanji)
- **Decoded:** `性難  'ブ難`
- **Purpose:** Short text (pre-menu-data)
- **Hex:** `ff 01 02 03 00 00 00 00 07 00 00 01 02 03`

### [404] 0x3C05D8-0x3C05E6

- **Size:** 14 bytes, 7 glyphs (3 kanji)
- **Decoded:** `性"  %ブ難`
- **Purpose:** Short text (pre-menu-data)
- **Hex:** `ff 01 02 00 00 00 00 00 05 00 00 01 02 03`

### [405] 0x3C05EE-0x3C05F8

- **Size:** 10 bytes, 5 glyphs (3 kanji)
- **Decoded:** `種 %ブ難`
- **Purpose:** Short text (pre-menu-data)
- **Hex:** `01 02 00 00 05 00 00 01 02 03`

### [406] 0x3C0602-0x3C060A

- **Size:** 8 bytes, 4 glyphs (2 kanji)
- **Decoded:** ` 'ブ難`
- **Purpose:** Short text (pre-menu-data)
- **Hex:** `00 00 07 00 00 01 02 03`

### [407] 0x3C06CC-0x3C06D8

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (pre-menu-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [408] 0x3C0844-0x3C0850

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (pre-menu-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [409] 0x3C0CA2-0x3C0CB0

- **Size:** 14 bytes, 7 glyphs (3 kanji)
- **Decoded:** `だけだ    `
- **Purpose:** Short text (pre-menu-data)
- **Hex:** `a8 00 78 00 a8 00 00 00 00 00 00 00 00 00`

### [410] 0x3C0D38-0x3C0D4C

- **Size:** 20 bytes, 10 glyphs (3 kanji)
- **Decoded:** `    ベ!  ブベ`
- **Purpose:** Medium text (pre-menu-data)
- **Hex:** `00 00 00 00 00 00 00 00 01 01 01 00 00 00 00 00 00 01 01 01`

### [411] 0x3C0D52-0x3C0D5E

- **Size:** 12 bytes, 6 glyphs (3 kanji)
- **Decoded:** `   ベベベ`
- **Purpose:** Short text (pre-menu-data)
- **Hex:** `00 00 00 00 00 00 01 01 01 01 01 01`

### [412] 0x3C0D74-0x3C0D7E

- **Size:** 10 bytes, 5 glyphs (2 kanji)
- **Decoded:** `   ブベ`
- **Purpose:** Short text (pre-menu-data)
- **Hex:** `00 00 00 00 00 00 00 01 01 01`

### [413] 0x3C0DA8-0x3C0DC2

- **Size:** 26 bytes, 13 glyphs (4 kanji)
- **Decoded:** `     ブ!  ベ ブブ`
- **Purpose:** Medium text (pre-menu-data)
- **Hex:** `00 00 00 00 00 00 00 00 00 00 00 01 01 00 00 00 00 00 01 01 00 00 00 01 00 01`

### [414] 0x3C1AC0-0x3C1AC8

- **Size:** 8 bytes, 4 glyphs (2 kanji)
- **Decoded:** `ベ  別`
- **Purpose:** Short text (pre-menu-data)
- **Hex:** `01 01 00 00 00 00 00 02`

### [415] 0x3C1BA0-0x3C1BA8

- **Size:** 8 bytes, 4 glyphs (2 kanji)
- **Decoded:** `ベ! 別`
- **Purpose:** Short text (pre-menu-data)
- **Hex:** `01 01 01 00 00 00 00 02`

### [416] 0x3C1C10-0x3C1C18

- **Size:** 8 bytes, 4 glyphs (2 kanji)
- **Decoded:** `ベ  別`
- **Purpose:** Short text (pre-menu-data)
- **Hex:** `01 01 00 00 00 00 00 02`

### [417] 0x3C2090-0x3C20A2

- **Size:** 18 bytes, 9 glyphs (5 kanji)
- **Decoded:** `ベプペョ    威`
- **Purpose:** Medium text (pre-menu-data)
- **Hex:** `01 01 05 01 06 01 0a 01 00 00 00 00 00 00 00 00 01 03`

### [418] 0x3C20A4-0x3C20AC

- **Size:** 8 bytes, 4 glyphs (4 kanji)
- **Decoded:** `ベプベポ`
- **Purpose:** Short text (pre-menu-data)
- **Hex:** `01 01 05 01 01 01 07 01`

### [419] 0x3C2F18-0x3C2F20

- **Size:** 8 bytes, 4 glyphs (2 kanji)
- **Decoded:** ` 王お `
- **Purpose:** Short text (pre-menu-data)
- **Hex:** `00 00 db 01 74 00 00 00`

### [420] 0x3C2F30-0x3C2F44

- **Size:** 20 bytes, 10 glyphs (3 kanji)
- **Decoded:** `     覚 仲 覚`
- **Purpose:** Medium text (pre-menu-data)
- **Hex:** `00 00 00 00 00 00 00 00 00 00 a3 02 00 00 a4 02 00 00 a3 02`

### [421] 0x3C2F48-0x3C2F5E

- **Size:** 22 bytes, 11 glyphs (4 kanji)
- **Decoded:** ` 仲!覚 [?476]N  味 `
- **Purpose:** Medium text (pre-menu-data)
- **Hex:** `00 00 a4 02 01 00 a3 02 00 00 dc 01 2e 00 00 00 00 00 5c 02 00 00`

### [422] 0x3C2F70-0x3C2F80

- **Size:** 16 bytes, 8 glyphs (4 kanji)
- **Decoded:** ` 鑑 異 鑑 異`
- **Purpose:** Medium text (pre-menu-data)
- **Hex:** `00 00 a5 02 00 00 a6 02 00 00 a5 02 00 00 a6 02`

### [423] 0x3C2F84-0x3C2F96

- **Size:** 18 bytes, 9 glyphs (3 kanji)
- **Decoded:** `!鑑 噂O  持 `
- **Purpose:** Medium text (pre-menu-data)
- **Hex:** `01 00 a5 02 00 00 dd 01 2f 00 00 00 00 00 5d 02 00 00`

### [424] 0x3C2FA8-0x3C2FCE

- **Size:** 38 bytes, 19 glyphs (8 kanji)
- **Decoded:** ` 殿 解 殿 解!解!殿 彼P  使 `
- **Purpose:** Medium text (pre-menu-data)
- **Hex:** `00 00 a7 02 00 00 a8 02 00 00 a7 02 00 00 a8 02 01 00 a8 02 01 00 a7 02 00 00 de`

### [425] 0x3C2FE0-0x3C2FF0

- **Size:** 16 bytes, 8 glyphs (4 kanji)
- **Decoded:** ` [?681] 功 [?681] 功`
- **Purpose:** Medium text (pre-menu-data)
- **Hex:** `00 00 a9 02 00 00 aa 02 00 00 a9 02 00 00 aa 02`

### [426] 0x3C2FF4-0x3C3006

- **Size:** 18 bytes, 9 glyphs (3 kanji)
- **Decoded:** `![?681] 対Q  稼 `
- **Purpose:** Medium text (pre-menu-data)
- **Hex:** `01 00 a9 02 00 00 df 01 31 00 00 00 00 00 5f 02 00 00`

### [427] 0x3C5366-0x3C5370

- **Size:** 10 bytes, 5 glyphs (2 kanji)
- **Decoded:** `C初D幸D`
- **Purpose:** Short text (mid-data)
- **Hex:** `23 00 60 01 24 00 d0 02 24 00`

### [428] 0x3C735C-0x3C7364

- **Size:** 8 bytes, 4 glyphs (2 kanji)
- **Decoded:** `  ブあ`
- **Purpose:** Short text (mid-data)
- **Hex:** `00 00 00 00 00 01 70 00`

### [429] 0x3C81E0-0x3C81E8

- **Size:** 8 bytes, 4 glyphs (2 kanji)
- **Decoded:** ` ♥ ♥`
- **Purpose:** Short text (data)
- **Hex:** `00 00 5f 00 00 00 5f 00`

### [430] 0x3C81F8-0x3C8210

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** ` [?96] [?96] [?97] [?97] [?98] [?98]`
- **Purpose:** Medium text (data)
- **Hex:** `00 00 60 00 00 00 60 00 00 00 61 00 00 00 61 00 00 00 62 00 00 00 62 00`

### [431] 0x3C8218-0x3C8258

- **Size:** 64 bytes, 32 glyphs (16 kanji)
- **Decoded:** ` [?99] [?99] [?100] [?100] [?101] [?101] [?102] [?102] [?103] [?103] [?104] [?104] [?105] [?105] [?106] [?106]`
- **Purpose:** Long text string (data)
- **Hex:** `00 00 63 00 00 00 63 00 00 00 64 00 00 00 64 00 00 00 65 00 00 00 65 00 00 00 66`

### [432] 0x3C8268-0x3C8270

- **Size:** 8 bytes, 4 glyphs (2 kanji)
- **Decoded:** ` [?107] [?107]`
- **Purpose:** Short text (data)
- **Hex:** `00 00 6b 00 00 00 6b 00`

### [433] 0x3C8278-0x3C82B0

- **Size:** 56 bytes, 28 glyphs (12 kanji)
- **Decoded:** `     [?108] [?108] ％ ％ [?110] [?110] [?111] [?111] あ あ い い`
- **Purpose:** Long text string (data)
- **Hex:** `00 00 00 00 00 00 00 00 00 00 6c 00 00 00 6c 00 00 00 6d 00 00 00 6d 00 00 00 6e`

### [434] 0x3C82C8-0x3C82D8

- **Size:** 16 bytes, 8 glyphs (4 kanji)
- **Decoded:** ` う う え え`
- **Purpose:** Medium text (data)
- **Hex:** `00 00 72 00 00 00 72 00 00 00 73 00 00 00 73 00`

### [435] 0x3C82E8-0x3C8328

- **Size:** 64 bytes, 32 glyphs (16 kanji)
- **Decoded:** ` お お か か き き く く け け こ こ さ さ し し`
- **Purpose:** Long text string (data)
- **Hex:** `00 00 74 00 00 00 74 00 00 00 75 00 00 00 75 00 00 00 76 00 00 00 76 00 00 00 77`

### [436] 0x3C8350-0x3C8370

- **Size:** 32 bytes, 16 glyphs (8 kanji)
- **Decoded:** ` す す せ せ そ そ た た`
- **Purpose:** Medium text (data)
- **Hex:** `00 00 7c 00 00 00 7c 00 00 00 7d 00 00 00 7d 00 00 00 7e 00 00 00 7e 00 00 00 7f`

### [437] 0x3C8390-0x3C8418

- **Size:** 136 bytes, 68 glyphs (34 kanji)
- **Decoded:** ` ち ち つ つ て て と と な な に に ぬ!ぬ ね ね の!の は は ひ ひ ふ ふ へ へ ほ ほ ま ま み み む む`
- **Purpose:** Long text string (data)
- **Hex:** `00 00 80 00 00 00 80 00 00 00 81 00 00 00 81 00 00 00 82 00 00 00 82 00 00 00 83`

### [438] 0x3C93AE-0x3C93BA

- **Size:** 12 bytes, 6 glyphs (4 kanji)
- **Decoded:** `Oエミ}リア`
- **Purpose:** Short text (data)
- **Hex:** `2f 00 c4 00 e0 00 5d 00 e8 00 c1 00`

### [439] 0x3C93C0-0x3C93C8

- **Size:** 8 bytes, 4 glyphs (3 kanji)
- **Decoded:** `リュ}ト`
- **Purpose:** Short text (data)
- **Hex:** `e8 00 09 01 5d 00 d4 00`

### [440] 0x3C9A34-0x3C9DA0

- **Size:** 876 bytes, 438 glyphs (328 kanji)
- **Decoded:** `  vみクベ名与  wむケボ盗苦  xめコパ武居  yもサピ炎対  zやシプ算道  {ゆスペ人鉄  |よセポ心店      }らソャ頼度~りタュ落転    そゃギ士仰町たゅグ迷少物ちょゲ野多復  つぁゴ神紹子  ♥るチョ力[?380]  [?96]れツァ多傷      [?98]わトゥ法長[?99]をナェ短二[?100]んニォ上地[?101]がヌッ賊[?386][?102]ぎネヴ言重[?103]ぐノ祠限呪[?104]げハ小装払      [?105]ごヒ手[?333][?390][?106]ざフ宮崩古[?107]じヘ防差報[?108]ずホ攻教半％ぜマ騎中彼[?110]ぞミ使一戻[?111]だム向気教      あぢメ行立毒いづモ聖不帰うでヤ罰事頼えどユ戦持理おばヨ者悔侍かびラ鎧邪支きぶリ悪力水      くべル動骨像けぼレ飾光集こぱロ法女封さぴワ魔得告しぷヲ辺除落すぺン大初願せぽガ王暗秘      てぃザ石外回とぅジ魔銀宿なぇズ依場直にぉゼ兵然女ぬっゾ飲情書ね[?192]ダ切信[?420]    のアヂ奥[?364]編はイヅ信両古ひウデ忍影良ふエド団行短ぬっバ飲情約ほカビ腕見束まキブ開成[?427]      9 : ; < = > ? @ A B C D う       `
- **Purpose:** Status effect (post-chargen)
- **Hex:** `00 00 00 00 56 00 8f 00 c8 00 01 01 3a 01 73 01 00 00 00 00 57 00 90 00 c9 00 02`

### [441] 0x3CBED4-0x3CBEE0

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [442] 0x3CBFF4-0x3CC000

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [443] 0x3CC114-0x3CC12C

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ !$ち0ち8`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 01 00 04 00 80 00 10 00 80 00 18 00`

### [444] 0x3CC184-0x3CC190

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [445] 0x3CC448-0x3CC460

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ !$[?96]0[?96]だ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 01 00 04 00 60 00 10 00 60 00 a8 00`

### [446] 0x3CC480-0x3CC498

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    !&0ゅpゅ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 01 00 06 00 10 00 b8 00 50 00 b8 00`

### [447] 0x3CC49C-0x3CC4B4

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ !'[?96]ゅ  `
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 01 00 07 00 60 00 b8 00 00 00 00 00`

### [448] 0x3CC4D4-0x3CC4E0

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [449] 0x3CC4F0-0x3CC508

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ      ,$[?96][?192]`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 00 00 00 00 0c 00 04 00 60 00 c0 00`

### [450] 0x3CC568-0x3CC57A

- **Size:** 18 bytes, 9 glyphs (3 kanji)
- **Decoded:** `ブブ     eつ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 00 00 45 00 81 00`

### [451] 0x3CC584-0x3CC596

- **Size:** 18 bytes, 9 glyphs (3 kanji)
- **Decoded:** `ブブ     fじ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 00 00 46 00 a4 00`

### [452] 0x3CC5A0-0x3CC5B2

- **Size:** 18 bytes, 9 glyphs (3 kanji)
- **Decoded:** `ブブ     gキ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 00 00 47 00 c7 00`

### [453] 0x3CC5BC-0x3CC5CE

- **Size:** 18 bytes, 9 glyphs (3 kanji)
- **Decoded:** `ブブ     hレ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 00 00 48 00 ea 00`

### [454] 0x3CC69C-0x3CC6B4

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    !$ブ0ブ8`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 01 00 04 00 00 01 10 00 00 01 18 00`

### [455] 0x3CC728-0x3CC734

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [456] 0x3CC744-0x3CC758

- **Size:** 20 bytes, 10 glyphs (3 kanji)
- **Decoded:** `ブブ    ,$ビL`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 0c 00 04 00 ff 00 2c 00`

### [457] 0x3CC7B8-0x3CC7C4

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [458] 0x3CC80C-0x3CC818

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [459] 0x3CC8FC-0x3CC908

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ  $ `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00`

### [460] 0x3CCA94-0x3CCAAC

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ !# [?101] け`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 01 00 03 00 00 00 65 00 00 00 78 00`

### [461] 0x3CCACC-0x3CCAE4

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    !&0のべの`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 01 00 06 00 10 00 88 00 b0 00 88 00`

### [462] 0x3CCB58-0x3CCB64

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [463] 0x3CCB74-0x3CCB88

- **Size:** 20 bytes, 10 glyphs (4 kanji)
- **Decoded:** `ブブ    ,$[?192]へ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 0c 00 04 00 c0 00 8c 00`

### [464] 0x3CCC3C-0x3CCC48

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ  $ `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00`

### [465] 0x3CCDF0-0x3CCE08

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    !Dの|ミ|`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 01 00 24 00 88 00 5c 00 e0 00 5c 00`

### [466] 0x3CCE98-0x3CCEA4

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ  $ `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00`

### [467] 0x3CCFCC-0x3CCFE4

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    !Dの\ミ\`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 01 00 24 00 88 00 3c 00 e0 00 3c 00`

### [468] 0x3CD020-0x3CD02C

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ  $ `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00`

### [469] 0x3CD15C-0x3CD174

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    !Dの\ミ\`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 01 00 24 00 88 00 3c 00 e0 00 3c 00`

### [470] 0x3CD1B0-0x3CD1BC

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ  $ `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00`

### [471] 0x3CD2EC-0x3CD304

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    !Dの\ミ\`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 01 00 24 00 88 00 3c 00 e0 00 3c 00`

### [472] 0x3CD340-0x3CD34C

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ  $ `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00`

### [473] 0x3CD47C-0x3CD494

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    !Dの\ミ\`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 01 00 24 00 88 00 3c 00 e0 00 3c 00`

### [474] 0x3CD4D0-0x3CD4DC

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ  $ `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00`

### [475] 0x3CD60C-0x3CD624

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    !Dの\ミ\`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 01 00 24 00 88 00 3c 00 e0 00 3c 00`

### [476] 0x3CD660-0x3CD66C

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ  $ `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00`

### [477] 0x3CD6D8-0x3CD6E4

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [478] 0x3CD6F4-0x3CD708

- **Size:** 20 bytes, 10 glyphs (4 kanji)
- **Decoded:** `ブブ    (,[?108][?96]`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 08 00 0c 00 6c 00 60 00`

### [479] 0x3CD788-0x3CD794

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [480] 0x3CD830-0x3CD83C

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ #  `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 03 00 00 00 00 00`

### [481] 0x3CD904-0x3CD916

- **Size:** 18 bytes, 9 glyphs (3 kanji)
- **Decoded:** `ブブ     fあ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 00 00 46 00 70 00`

### [482] 0x3CD920-0x3CD932

- **Size:** 18 bytes, 9 glyphs (3 kanji)
- **Decoded:** `ブブ     gの`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 00 00 47 00 88 00`

### [483] 0x3CD93C-0x3CD94E

- **Size:** 18 bytes, 9 glyphs (3 kanji)
- **Decoded:** `ブブ     hぐ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 00 00 48 00 a0 00`

### [484] 0x3CD990-0x3CD9A8

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    !$ゅ0ゅ2`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 01 00 04 00 b8 00 10 00 b8 00 12 00`

### [485] 0x3CD9E4-0x3CD9F0

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [486] 0x3CDA40-0x3CDA52

- **Size:** 18 bytes, 9 glyphs (3 kanji)
- **Decoded:** `ブブ     Kち`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 00 00 2b 00 80 00`

### [487] 0x3CDBC8-0x3CDBDA

- **Size:** 18 bytes, 9 glyphs (3 kanji)
- **Decoded:** `ブブ    !<[?104]`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 01 00 1c 00 68 00`

### [488] 0x3CDC70-0x3CDC88

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    !<[?104][?105]  `
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 01 00 1c 00 68 00 69 00 00 00 00 00`

### [489] 0x3CDC8C-0x3CDCA4

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    !<[?104]こ  `
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 01 00 1c 00 68 00 79 00 00 00 00 00`

### [490] 0x3CDD18-0x3CDD30

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ !$ぐ0ぐけ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 01 00 04 00 a0 00 10 00 a0 00 78 00`

### [491] 0x3CDD50-0x3CDD68

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    !&0のむの`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 01 00 06 00 10 00 88 00 90 00 88 00`

### [492] 0x3CDD6C-0x3CDD84

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ !'ぐの  `
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 01 00 07 00 a0 00 88 00 00 00 00 00`

### [493] 0x3CDD88-0x3CDD94

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [494] 0x3CDDA4-0x3CDDB8

- **Size:** 20 bytes, 10 glyphs (4 kanji)
- **Decoded:** `ブブ    ($ぜむ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 08 00 04 00 a6 00 90 00`

### [495] 0x3CDE50-0x3CDE5C

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [496] 0x3CDEE4-0x3CDEFC

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    !Dの|ミ|`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 01 00 24 00 88 00 5c 00 e0 00 5c 00`

### [497] 0x3CDF38-0x3CDF44

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ  $ `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00`

### [498] 0x3CDFA8-0x3CDFB4

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [499] 0x3CDFC4-0x3CDFD6

- **Size:** 18 bytes, 9 glyphs (3 kanji)
- **Decoded:** `ブブ     Yち`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 00 00 39 00 80 00`

### [500] 0x3CDFE0-0x3CDFF2

- **Size:** 18 bytes, 9 glyphs (3 kanji)
- **Decoded:** `ブブ    !Cあ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 01 00 23 00 70 00`

### [501] 0x3CDFFC-0x3CE00E

- **Size:** 18 bytes, 9 glyphs (3 kanji)
- **Decoded:** `ブブ    !Dち`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 01 00 24 00 80 00`

### [502] 0x3CE018-0x3CE02A

- **Size:** 18 bytes, 9 glyphs (3 kanji)
- **Decoded:** `ブブ  $ !Eべ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 01 00 25 00 b0 00`

### [503] 0x3CE114-0x3CE120

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [504] 0x3CE410-0x3CE428

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ !# [?100] [?192]`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 01 00 03 00 00 00 64 00 00 00 c0 00`

### [505] 0x3CE42C-0x3CE444

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ !$けHけ[?192]`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 01 00 04 00 78 00 28 00 78 00 c0 00`

### [506] 0x3CE4F0-0x3CE508

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    !&0タ[?104]タ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 01 00 06 00 10 00 d0 00 68 00 d0 00`

### [507] 0x3CE50C-0x3CE524

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ !'けタ  `
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 01 00 07 00 78 00 d0 00 00 00 00 00`

### [508] 0x3CE544-0x3CE550

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [509] 0x3CE560-0x3CE578

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ      ,$すト`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 00 00 00 00 0c 00 04 00 7c 00 d4 00`

### [510] 0x3CE5A0-0x3CE5B2

- **Size:** 18 bytes, 9 glyphs (4 kanji)
- **Decoded:** `ブブ    #[?101]だ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 03 00 65 00 a8 00`

### [511] 0x3CE824-0x3CE83C

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    !2けタ  `
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 01 00 12 00 78 00 d0 00 00 00 00 00`

### [512] 0x3CE8CC-0x3CE8E4

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ !# あ [?192]`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 01 00 03 00 00 00 70 00 00 00 c0 00`

### [513] 0x3CE8E8-0x3CE900

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ !$ネHネ[?192]`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 01 00 04 00 d8 00 28 00 d8 00 c0 00`

### [514] 0x3CE9AC-0x3CE9C4

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    !&0タクタ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 01 00 06 00 10 00 d0 00 c8 00 d0 00`

### [515] 0x3CE9C8-0x3CE9E0

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ !'ネタ  `
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 01 00 07 00 d8 00 d0 00 00 00 00 00`

### [516] 0x3CEA00-0x3CEA0C

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [517] 0x3CEAEC-0x3CEAF8

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [518] 0x3CEB84-0x3CEB9C

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    $>0べべべ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 b0 00 b0 00`

### [519] 0x3CEBA0-0x3CEBAC

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ  $ `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00`

### [520] 0x3CEC54-0x3CEC6C

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<べ0べぐ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 b0 00 10 00 b0 00 a0 00`

### [521] 0x3CEC8C-0x3CECA4

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    $>0べぐべ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 a0 00 b0 00`

### [522] 0x3CECA8-0x3CECC0

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?べべ  `
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 b0 00 b0 00 00 00 00 00`

### [523] 0x3CECC4-0x3CECD0

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [524] 0x3CECE0-0x3CECF8

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ      $$ゅぷ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 00 00 00 00 04 00 04 00 b8 00 b4 00`

### [525] 0x3CED3C-0x3CED54

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9べ エ `
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 b0 00 00 00 c4 00 00 00`

### [526] 0x3CED90-0x3CEDA8

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<ト0トぐ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 d4 00 10 00 d4 00 a0 00`

### [527] 0x3CEDC8-0x3CEDE0

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    $>0べむべ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 90 00 b0 00`

### [528] 0x3CEDE4-0x3CEDFC

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>べべエべ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 b0 00 b0 00 c4 00 b0 00`

### [529] 0x3CEE00-0x3CEE18

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?トべ  `
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 d4 00 b0 00 00 00 00 00`

### [530] 0x3CEE38-0x3CEE50

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $Eぐべ  `
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 25 00 a0 00 b0 00 00 00 00 00`

### [531] 0x3CEE54-0x3CEE60

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [532] 0x3CEEAC-0x3CEEC4

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9お む `
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 74 00 00 00 90 00 00 00`

### [533] 0x3CEEC8-0x3CEEE0

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9べ エ `
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 b0 00 00 00 c4 00 00 00`

### [534] 0x3CEF1C-0x3CEF34

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<ト0トぐ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 d4 00 10 00 d4 00 a0 00`

### [535] 0x3CEF54-0x3CEF6C

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    $>0べむべ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 90 00 b0 00`

### [536] 0x3CEF70-0x3CEF88

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>べべエべ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 b0 00 b0 00 c4 00 b0 00`

### [537] 0x3CEF8C-0x3CEFA4

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?トべ  `
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 d4 00 b0 00 00 00 00 00`

### [538] 0x3CEFFC-0x3CF014

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $Eぐべ  `
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 25 00 a0 00 b0 00 00 00 00 00`

### [539] 0x3CF034-0x3CF040

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ !  `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 01 00 00 00 00 00`

### [540] 0x3CF08C-0x3CF0A4

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9べ エ `
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 b0 00 00 00 c4 00 00 00`

### [541] 0x3CF0E0-0x3CF0F8

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<ト0トぐ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 d4 00 10 00 d4 00 a0 00`

### [542] 0x3CF118-0x3CF130

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $>0べLべ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 2c 00 b0 00`

### [543] 0x3CF134-0x3CF14C

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>おべむべ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 74 00 b0 00 90 00 b0 00`

### [544] 0x3CF150-0x3CF168

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>べべエべ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 b0 00 b0 00 c4 00 b0 00`

### [545] 0x3CF16C-0x3CF184

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?トべ  `
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 d4 00 b0 00 00 00 00 00`

### [546] 0x3CF1DC-0x3CF1F4

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $Eぐべ  `
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 25 00 a0 00 b0 00 00 00 00 00`

### [547] 0x3CF214-0x3CF220

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ "  `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 02 00 00 00 00 00`

### [548] 0x3CF26C-0x3CF284

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9お む `
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 74 00 00 00 90 00 00 00`

### [549] 0x3CF288-0x3CF2A0

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9べ エ `
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 b0 00 00 00 c4 00 00 00`

### [550] 0x3CF2DC-0x3CF2F4

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<ト0トぐ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 d4 00 10 00 d4 00 a0 00`

### [551] 0x3CF314-0x3CF32C

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $>0べLべ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 2c 00 b0 00`

### [552] 0x3CF330-0x3CF348

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>おべむべ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 74 00 b0 00 90 00 b0 00`

### [553] 0x3CF34C-0x3CF364

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>べべエべ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 b0 00 b0 00 c4 00 b0 00`

### [554] 0x3CF368-0x3CF380

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?トべ  `
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 d4 00 b0 00 00 00 00 00`

### [555] 0x3CF410-0x3CF428

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $Eぐべ  `
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 25 00 a0 00 b0 00 00 00 00 00`

### [556] 0x3CF464-0x3CF470

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ "  `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 02 00 00 00 00 00`

### [557] 0x3CF480-0x3CF498

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ      %%ハゃ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 00 00 00 00 05 00 05 00 da 00 b7 00`

### [558] 0x3CF514-0x3CF52C

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<べ0べぐ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 b0 00 10 00 b0 00 a0 00`

### [559] 0x3CF54C-0x3CF564

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    $>0べぐべ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 a0 00 b0 00`

### [560] 0x3CF568-0x3CF580

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?べべ  `
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 b0 00 b0 00 00 00 00 00`

### [561] 0x3CF584-0x3CF590

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [562] 0x3CF5DC-0x3CF5F4

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9お ぐ `
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 74 00 00 00 a0 00 00 00`

### [563] 0x3CF630-0x3CF648

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<べ0べぐ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 b0 00 10 00 b0 00 a0 00`

### [564] 0x3CF668-0x3CF680

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ    $>0べぐべ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 a0 00 b0 00`

### [565] 0x3CF684-0x3CF69C

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?べべ  `
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 b0 00 b0 00 00 00 00 00`

### [566] 0x3CF6F4-0x3CF700

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ !  `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 01 00 00 00 00 00`

### [567] 0x3CF784-0x3CF79C

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<べ0べぐ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 b0 00 10 00 b0 00 a0 00`

### [568] 0x3CF7BC-0x3CF7D4

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $>0べLべ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 2c 00 b0 00`

### [569] 0x3CF7D8-0x3CF7F0

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>おべぐべ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 74 00 b0 00 a0 00 b0 00`

### [570] 0x3CF7F4-0x3CF80C

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?べべ  `
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 b0 00 b0 00 00 00 00 00`

### [571] 0x3CF864-0x3CF870

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ "  `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 02 00 00 00 00 00`

### [572] 0x3CF8BC-0x3CF8D4

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $9お ぐ `
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 19 00 74 00 00 00 a0 00 00 00`

### [573] 0x3CF910-0x3CF928

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $<べ0べぐ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1c 00 b0 00 10 00 b0 00 a0 00`

### [574] 0x3CF948-0x3CF960

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $>0べLべ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 1e 00 10 00 b0 00 2c 00 b0 00`

### [575] 0x3CF964-0x3CF97C

- **Size:** 24 bytes, 12 glyphs (6 kanji)
- **Decoded:** `ブブ  $ $>おべぐべ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1e 00 74 00 b0 00 a0 00 b0 00`

### [576] 0x3CF980-0x3CF998

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ  $ $?べべ  `
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 1f 00 b0 00 b0 00 00 00 00 00`

### [577] 0x3CFA44-0x3CFA50

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ "  `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 02 00 00 00 00 00`

### [578] 0x3CFA60-0x3CFA78

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ      %%ぽゃ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 00 00 00 00 05 00 05 00 b6 00 b7 00`

### [579] 0x3CFB2C-0x3CFB44

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $&0あ`あ`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 06 00 10 00 70 00 40 00 70 00`

### [580] 0x3CFB64-0x3CFB70

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [581] 0x3CFC84-0x3CFC9C

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ    $!じ 顔 `
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 04 00 01 00 a4 00 00 00 c8 01 00 00`

### [582] 0x3CFCD8-0x3CFCF0

- **Size:** 24 bytes, 12 glyphs (5 kanji)
- **Decoded:** `ブブ  $ $$込0込す`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00 04 00 04 00 d8 01 10 00 d8 01 7c 00`

### [583] 0x3CFCF4-0x3CFD00

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ  $ `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00`

### [584] 0x3CFD10-0x3CFD28

- **Size:** 24 bytes, 12 glyphs (4 kanji)
- **Decoded:** `ブブ      ((中お`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00 00 00 00 00 08 00 08 00 d6 01 74 00`

### [585] 0x3CFDA4-0x3CFDB0

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ  $ `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 04 00 00 00`

### [586] 0x3D01BA-0x3D03EA

- **Size:** 560 bytes, 280 glyphs (93 kanji)
- **Decoded:** `''*.*      :'A*K*]'d*n*[?96]'[?103]*い*と'ひ*ゆ*ぜ'ば*ゃ*ケ'タ*ハ*ワ'ゴ*ド*      2'A*H*U'd*k*x'[?103]*[?110]*し'ひ*め*が'ば*ぷ*ア'タ*ヌ*ヤ'ゴ*ヂ*      <0I0V0c0p0}0[?106]0く0な0      000@0P0`0p0[?96]0あ0ち0む0ぐ    000@0P0`0p0[?96]    000@0P0`0p0[?96]0あ0ち0む0ぐ    べ0[?192]0シ0べ@[?192]@シ@べP[?192]PシPべ`[?192]`シ`べp[?192]pシpべ[?96][?192][?96]シ[?96]べあ[?192]あシあべち[?192]ちシちべむ[?192]むシむべぐ[?192]ぐシぐ    000@0P0`0p0[?96]0あ0ち0む0ぐ$`
- **Purpose:** Long text string (late-data)
- **Hex:** `07 00 07 00 0a 00 0e 00 0a 00 00 00 00 00 00 00 00 00 00 00 00 00 1a 00 07 00 21`

### [587] 0x3D0400-0x3D06EA

- **Size:** 746 bytes, 373 glyphs (112 kanji)
- **Decoded:** `p#      6(5689N(M6P9f(e6h9~(}6[?96]9き(か6け9ま(ほ6む9ぜ(ず6だ9      1(5649I(M6L9a(e6d9y(}6|9い(か6お9は(ほ6へ9げ(ず6じ9      6(5689N(M6P9f(e6h9~(}6[?96]9き(か6け9ま(ほ6む9ぜ(ず6だ9      1(5649I(M6L9a(e6d9y(}6|9い(か6お9は(ほ6へ9げ(ず6じ9      Z[\]^_`abcdefghij       ト+ザ+手+信+立+苦+像+抜+ト7ザ7手7信7立7苦7像7抜7ぷ7  ぷ*っ*コ*      000@0P0`0p0[?96]0あ0ち0む0ぐ    ふ0ぎ0ぞ0ふ@ぎ@ぞ@ふPぎPぞPふ`ぎ`ぞ`ふpぎpぞpふ[?96]ぎ[?96]ぞ[?96]ふあぎあぞあふちぎちぞちふむぎむぞむふぐぎぐぞぐ      #[?100]  $[?100][?104] $[?100]@`
- **Purpose:** Long text string (late-data)
- **Hex:** `50 00 03 00 00 00 00 00 00 00 00 00 00 00 00 00 16 00 08 00 15 00 16 00 18 00 19`

### [588] 0x3D08D4-0x3D0BD0

- **Size:** 764 bytes, 382 glyphs (142 kanji)
- **Decoded:** `$8$X$x$け$る$ゅ  000@0P0`0p0[?96]0あ0ち0む0ぐL(n0v(  T@rH[?96]@  TTr\[?96]T  Thrp[?96]h  T[?100]r[?108][?96][?100]  Tけrち[?96]け  Tへrゆ[?96]へ  Tぐrだ[?96]ぐ  Tぷrぅ[?96]ぷ  Tクrタ[?96]ク      L(n0v(へ(び0ぽ(    T@rH[?96]@ゆ@ぱH[?192]@    TTr\[?96]TゆTぱ\[?192]T    Thrp[?96]hゆhぱp[?192]h    T[?100]r[?108][?96][?100]ゆ[?100]ぱ[?108][?192][?100]    Tけrち[?96]けゆけぱち[?192]け    Tへrゆ[?96]へゆへぱゆ[?192]へ    Tぐrだ[?96]ぐゆぐぱだ[?192]ぐ    Tぷrぅ[?96]ぷゆぷぱぅ[?192]ぷ    Tクrタ[?96]クゆクぱタ[?192]クL(n0v(  T@rH[?96]@  TTr\[?96]T  Thrp[?96]h  T[?100]r[?108][?96][?100]  Tけrち[?96]け  Tへrゆ[?96]へ  Tぐrだ[?96]ぐ  Tぷrぅ[?96]ぷ  Tクrタ[?96]ク      000@0P0`0p0[?96]0あ0ち0む0ぐ    `
- **Purpose:** Long text string (late-data)
- **Hex:** `04 00 18 00 04 00 38 00 04 00 58 00 04 00 78 00 04 00 98 00 04 00 b8 00 00 00 00`

### [589] 0x3D443C-0x3D4448

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [590] 0x3D4474-0x3D447C

- **Size:** 8 bytes, 4 glyphs (2 kanji)
- **Decoded:** `ちぐ  `
- **Purpose:** Short text (late-data)
- **Hex:** `80 00 a0 00 00 00 00 00`

### [591] 0x3D4480-0x3D448C

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [592] 0x3D44B4-0x3D44BC

- **Size:** 8 bytes, 4 glyphs (2 kanji)
- **Decoded:** `ちぐ  `
- **Purpose:** Short text (late-data)
- **Hex:** `80 00 a0 00 00 00 00 00`

### [593] 0x3D44C0-0x3D44CC

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [594] 0x3D44F4-0x3D44FC

- **Size:** 8 bytes, 4 glyphs (2 kanji)
- **Decoded:** `ちぐ  `
- **Purpose:** Short text (late-data)
- **Hex:** `80 00 a0 00 00 00 00 00`

### [595] 0x3D4500-0x3D450C

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [596] 0x3D45B0-0x3D45BC

- **Size:** 12 bytes, 6 glyphs (2 kanji)
- **Decoded:** `ブブ    `
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 00 01 00 00 00 00 00 00 00 00`

### [597] 0x3D67A2-0x3D67B2

- **Size:** 16 bytes, 8 glyphs (4 kanji)
- **Decoded:** ` ブ憶ち 憶  `
- **Purpose:** Medium text (late-data)
- **Hex:** `00 00 00 01 c0 01 80 00 00 00 c0 01 00 00 00 00`

### [598] 0x3D6B78-0x3D6B86

- **Size:** 14 bytes, 7 glyphs (3 kanji)
- **Decoded:** `!ベ  ちち `
- **Purpose:** Short text (late-data)
- **Hex:** `01 00 01 01 00 00 00 00 80 00 80 00 00 00`

### [599] 0x3D6B8C-0x3D6B9A

- **Size:** 14 bytes, 7 glyphs (3 kanji)
- **Decoded:** `"ベ  ちち `
- **Purpose:** Short text (late-data)
- **Hex:** `02 00 01 01 00 00 00 00 80 00 80 00 00 00`

### [600] 0x3D6BA0-0x3D6BAE

- **Size:** 14 bytes, 7 glyphs (3 kanji)
- **Decoded:** `#ベ  ちち `
- **Purpose:** Short text (late-data)
- **Hex:** `03 00 01 01 00 00 00 00 80 00 80 00 00 00`

### [601] 0x3DC7C6-0x3DC7D8

- **Size:** 18 bytes, 9 glyphs (3 kanji)
- **Decoded:** `i j鎧j同j園j`
- **Purpose:** Medium text (late-data)
- **Hex:** `49 00 00 00 4a 00 20 01 4a 00 40 02 4a 00 60 03 4a 00`

### [602] 0x3DD800-0x3DDB18

- **Size:** 792 bytes, 396 glyphs (121 kanji)
- **Decoded:** `ご ダ と [?110] n d 5 I デ G w チ ジ T ヘ [?192] ヒ [?98] よ れ \ c む a バ q [?99] で ホ ぃ オ [?97] ゃ D [?110] Z b m ツ ミ & i N レ ) チ も < バ = ロ < ぼ I ぞ ^ リ て U ジ N ぃ d な ル を あ F ぷ ♥ そ a Y め ニ Y と s Y ザ を な ♥ ふ ぇ ダ H [ ? ゾ り ビ ホ % る / ガ O 1 ふ z * ％ ? ％ V そ ソ G サ ) ゃ o f _ [?102] が ♥ レ M か G ぁ キ ロ ユ グ し ] ' Y ゼ ひ r も レ [?107] ヅ ♥ ぼ ? ほ } ( v # P f デ し [?107] で ギ ソ ぅ @ ろ ザ V = ぢ モ め [?97] ~ ヨ ; ( [?101] れ に ♥ 4 ぐ [?104] ` ほ ビ ネ ち m え G Q & & 5 v コ え だ ケ [?96] メ し [?192] へ [?107] `
- **Purpose:** Long text string (late-data)
- **Hex:** `a2 00 00 00 f9 00 00 00 83 00 00 00 6e 00 00 00 4e 00 00 00 44 00 00 00 15 00 00`

### [603] 0x3DDC40-0x3DDC48

- **Size:** 8 bytes, 4 glyphs (4 kanji)
- **Decoded:** `ブ族下下`
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 02 02 03 03 03 03`

### [604] 0x3DDD40-0x3DDD48

- **Size:** 8 bytes, 4 glyphs (4 kanji)
- **Decoded:** `ブ族下下`
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 02 02 03 03 03 03`

### [605] 0x3DDE40-0x3DDE48

- **Size:** 8 bytes, 4 glyphs (4 kanji)
- **Decoded:** `ブ族下下`
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 02 02 03 03 03 03`

### [606] 0x3DDF40-0x3DDF48

- **Size:** 8 bytes, 4 glyphs (4 kanji)
- **Decoded:** `ブ族下下`
- **Purpose:** Short text (late-data)
- **Hex:** `00 01 02 02 03 03 03 03`

### [607] 0x3DE0A0-0x3DE0B4

- **Size:** 20 bytes, 10 glyphs (10 kanji)
- **Decoded:** `ベベベベベベベベベベ`
- **Purpose:** Medium text (late-data)
- **Hex:** `01 01 01 01 01 01 01 01 01 01 01 01 01 01 01 01 01 01 01 01`

### [608] 0x3DE0C0-0x3DE0D4

- **Size:** 20 bytes, 10 glyphs (10 kanji)
- **Decoded:** `族族族族族族族族族族`
- **Purpose:** Medium text (late-data)
- **Hex:** `02 02 02 02 02 02 02 02 02 02 02 02 02 02 02 02 02 02 02 02`

### [609] 0x3DEF70-0x3DEF7A

- **Size:** 10 bytes, 5 glyphs (2 kanji)
- **Decoded:** ` ブけ  `
- **Purpose:** Short text (late-data)
- **Hex:** `00 00 00 01 78 00 00 00 00 00`

### [610] 0x3DF4F6-0x3DF510

- **Size:** 26 bytes, 13 glyphs (6 kanji)
- **Decoded:** `5タ6ゾ6上6血6幸6俺6`
- **Purpose:** Medium text (late-data)
- **Hex:** `15 00 d0 00 16 00 f8 00 16 00 48 01 16 00 80 02 16 00 d0 02 16 00 18 03 16 00`

### [611] 0x3EA35C-0x3EA364

- **Size:** 8 bytes, 4 glyphs (2 kanji)
- **Decoded:** `  穏街`
- **Purpose:** Short text (late-data)
- **Hex:** `00 00 00 00 2f 02 42 02`

### [612] 0x3EA588-0x3EA590

- **Size:** 8 bytes, 4 glyphs (2 kanji)
- **Decoded:** `ぐビ  `
- **Purpose:** Short text (late-data)
- **Hex:** `a0 00 ff 00 00 00 00 00`

### [613] 0x3EA7BC-0x3EA7C4

- **Size:** 8 bytes, 4 glyphs (2 kanji)
- **Decoded:** `  穏意`
- **Purpose:** Short text (late-data)
- **Hex:** `00 00 00 00 2f 02 a1 02`

### [614] 0x3EAE4C-0x3EAE54

- **Size:** 8 bytes, 4 glyphs (2 kanji)
- **Decoded:** `  穏意`
- **Purpose:** Short text (late-data)
- **Hex:** `00 00 00 00 2f 02 a1 02`

### [615] 0x3EAEBC-0x3EAEC4

- **Size:** 8 bytes, 4 glyphs (2 kanji)
- **Decoded:** `  穏街`
- **Purpose:** Short text (late-data)
- **Hex:** `00 00 00 00 2f 02 42 02`

### [616] 0x3F0896-0x3F08B0

- **Size:** 26 bytes, 13 glyphs (4 kanji)
- **Decoded:** `     時H顔H看H街H`
- **Purpose:** Medium text (late-data)
- **Hex:** `00 00 00 00 00 00 00 00 00 00 b0 01 28 00 c8 01 28 00 68 02 28 00 b0 02 28 00`

## Action Items

Clusters that likely need English replacement:

### Status effect (2 clusters)

- 0x3B3008: `    (     ( ( ( 0   8   0 ( 8 (   0 ( 0   8 ( 8 0 0 8 0 0 8 `
- 0x3C9A34: `  vみクベ名与  wむケボ盗苦  xめコパ武居  yもサピ炎対  zやシプ算道  {ゆスペ人鉄  |よセポ心店    `

### Stat (1 clusters)

- 0x3B3D90: ` '.6=DLSZbipw♥[?102]％かすとひめれぐぞびぺぅエサツノミランジドピァ祠使鎧大魔忍武力言中悔除外両苦転地`

### Long text string (13 clusters)

- 0x3B5DEA: `ョ+ $むブ%[?108]ベ"[?96]ボ![?96]パ けピ#[?108]プ+Pペ'\ポ)nャ*nュ(nョ&\ァ,\ィ`
- 0x3B5F3E: `3*3(6)/',+4      ? D@0EB(GA(FC8H VWXYZ   アヴあ[?192]AZaz09[?96`
- 0x3B7A1C: `ブブ        ふまへほみよるらりれ      2[1\3]4^`
- 0x3B7C32: `wxyz{|}~♥[?96][?97][?98][?99][?100][?101][?102][?103][?104][`
- 0x3BC928: `R   テトナニヌネノハヒフ      `
- 0x3C8218: ` [?99] [?99] [?100] [?100] [?101] [?101] [?102] [?102] [?103`
- 0x3C8278: `     [?108] [?108] ％ ％ [?110] [?110] [?111] [?111] あ あ い い`
- 0x3C82E8: ` お お か か き き く く け け こ こ さ さ し し`
- 0x3C8390: ` ち ち つ つ て て と と な な に に ぬ!ぬ ね ね の!の は は ひ ひ ふ ふ へ へ ほ ほ ま ま`
- 0x3D01BA: `''*.*      :'A*K*]'d*n*[?96]'[?103]*い*と'ひ*ゆ*ぜ'ば*ゃ*ケ'タ*ハ*ワ'ゴ*`
- 0x3D0400: `p#      6(5689N(M6P9f(e6h9~(}6[?96]9き(か6け9ま(ほ6む9ぜ(ず6だ9      `
- 0x3D08D4: `$8$X$x$け$る$ゅ  000@0P0`0p0[?96]0あ0ち0む0ぐL(n0v(  T@rH[?96]@  TT`
- 0x3DD800: `ご ダ と [?110] n d 5 I デ G w チ ジ T ヘ [?192] ヒ [?98] よ れ \ c む `

### Medium text (391 clusters)

- 0x3B6806: `ちブブ  ( =`
- 0x3B6822: `ちブブ  ( :`
- 0x3B6A0A: `ちブブ  ( :`
- 0x3B6B5A: `ちブブ  ( ;`
- 0x3B6C20: `ブブ    %"る0初``
- 0x3B6C80: `ブブ    %0(ち@ミ`
- 0x3B6CF0: `ブブ    %' ちぐミ`
- 0x3B6D50: `別ブ    %-(ち@ミ`
- 0x3B6DA4: `ブブ    %*ッ あ0`
- 0x3B6E30: `ブブ    )の`
- 0x3B7120: `ブブ    )のB`
- 0x3B7190: `"ブ  ( )のBし戦B`
- 0x3B720C: `ブブ    ([?99]bち  `
- 0x3B7228: `ブブ    (♥(ち  `
- 0x3B7244: `ブブ    ([?100]びち  `
- 0x3B7260: `ブブ    (♥うち  `
- 0x3B727C: `ブブ    ([?101]騎ち  `
- 0x3B7298: `ブブ    ([?96]ホち  `
- 0x3B72B4: `ブブ    ([?102]bニ  `
- 0x3B72D0: `ブブ    (♥(ニ  `
- 0x3B72EC: `ブブ    ([?103]びニ  `
- 0x3B7308: `ブブ    (♥うニ  `
- 0x3B7324: `ブブ    ([?104]騎ニ  `
- 0x3B7340: `ブブ    ([?96]ホニ  `
- 0x3B7460: `ブブ    (％h[?108]  `
- 0x3B747C: `ブブ    (えp[?108]子(`
- 0x3B7498: `ブブ  ( ([?108]帰[?108]  `
- 0x3B74F0: `ブブ    (％h[?108]  `
- 0x3B750C: `ブブ    (えp[?108]子(`
- 0x3B7528: `ブブ  ( ([?108]帰[?108]  `
- 0x3B7580: `ブブ    (％h[?108]  `
- 0x3B759C: `ブブ    (えp[?108]子(`
- 0x3B75B8: `ブブ  ( ([?108]帰[?108]  `
- 0x3B7610: `ブブ    (％h[?108]  `
- 0x3B762C: `ブブ    (えp[?108]子(`
- 0x3B7648: `ブブ  ( ([?108]帰[?108]  `
- 0x3B76A0: `ブブ    (％h[?108]  `
- 0x3B76BC: `ブブ    (えp[?108]子(`
- 0x3B76D8: `ブブ  ( ([?108]帰[?108]  `
- 0x3B7730: `ブブ    (％h[?108]  `
- 0x3B774C: `ブブ    (えp[?108]子(`
- 0x3B7768: `ブブ  ( ([?108]帰[?108]  `
- 0x3B77C0: `ブブ    ,ぎあH0べ`
- 0x3B77F8: `"ブ  ( )ね0Hあぐ`
- 0x3B7850: `ブブ    ,ぎあH0べ`
- 0x3B7888: `"ブ  ( )ね0Hあぐ`
- 0x3B78E0: `ブブ    %8込落  `
- 0x3B78FC: `ブブ    %:H落時@`
- 0x3B7934: `ブブ  ( %<込H@看`
- 0x3B7990: `ブブ    ,ぎあN0べ`
- 0x3B79C8: `"ブ  ( )ね0Nあぐ`
- 0x3B79E4: `"ブ  ( )の祠^pど`
- 0x3B7E74: `ブブ    $$ぷH`
- 0x3B81C8: `ブブ  $ !$[?96]0[?96]だ`
- 0x3B8200: `ブブ    !&0ゅpゅ`
- 0x3B821C: `ブブ  $ !'[?96]ゅ  `
- 0x3B8270: `ブブ      ,$[?96]ぉ`
- 0x3B83D4: `ブブ    $$ぷH`
- 0x3B86CC: `ブブ        `[?96]二鎧`
- 0x3B8764: `ブブ    CT@ッ`ッ`
- 0x3B880C: `ブブ    CZ@ッ`ッ`
- 0x3B8974: `ブブ  $ $<べ0べぐ`
- 0x3B89AC: `ブブ    $>0べぐべ`
- 0x3B89C8: `ブブ  $ $?べべ  `
- 0x3B8A3C: `ブブ  $ $9す ぐ `
- 0x3B8A90: `ブブ  $ $<べ0べぐ`
- 0x3B8AC8: `ブブ    $>0べぐべ`
- 0x3B8AE4: `ブブ  $ $?べべ  `
- 0x3B8B1C: `ブブ    $A[?100]`
- 0x3B8BE4: `ブブ  $ $<べ0べぐ`
- 0x3B8C1C: `ブブ    $>0べTべ`
- 0x3B8C38: `ブブ  $ $>すべぐべ`
- 0x3B8C54: `ブブ  $ $?べべ  `
- 0x3B8C8C: `ブブ    $C[?100]べ  `
- 0x3B8D1C: `ブブ  $ $9す ぐ `
- 0x3B8D70: `ブブ  $ $<べ0べぐ`
- 0x3B8DA8: `ブブ    $>0べTべ`
- 0x3B8DC4: `ブブ  $ $>すべぐべ`
- 0x3B8DE0: `ブブ  $ $?べべ  `
- 0x3B8E18: `ブブ    $A[?100]`
- 0x3B8E50: `ブブ    $C[?100]べ  `
- 0x3B8EC0: `ブブ      %%ゅぽ`
- 0x3B8FD4: `ブブ  $ $<ミ0ミぐ`
- 0x3B900C: `ブブ    $>0べタべ`
- 0x3B9028: `ブブ  $ $?ミべ  `
- 0x3B909C: `ブブ  $ $9ゆ タ `
- 0x3B90F0: `ブブ  $ $<ミ0ミぐ`
- 0x3B9128: `ブブ    $>0べタべ`
- 0x3B9144: `ブブ  $ $?ミべ  `
- 0x3B917C: `ブブ    $Aす`
- 0x3B9198: `ブブ    $e[?108]`
- 0x3B9244: `ブブ  $ $<ミ0ミぐ`
- 0x3B927C: `ブブ    $>0べlべ`
- 0x3B9298: `ブブ  $ $>ゆべタべ`
- 0x3B92B4: `ブブ  $ $?ミべ  `
- 0x3B92EC: `ブブ    $Cすべ  `
- 0x3B9308: `ブブ    $h[?108]ぷ  `
- 0x3B937C: `ブブ  $ $9ゆ タ `
- 0x3B93D0: `ブブ  $ $<ミ0ミぐ`
- 0x3B9408: `ブブ    $>0べlべ`
- 0x3B9424: `ブブ  $ $>ゆべタべ`
- 0x3B9440: `ブブ  $ $?ミべ  `
- 0x3B9478: `ブブ    $Aす`
- 0x3B94B0: `ブブ    $Cすべ  `
- 0x3B94CC: `ブブ    $e[?108]`
- 0x3B94E8: `ブブ !  $h[?108]ぷ  `
- 0x3B9520: `ブブ      $$ヨぷ`
- 0x3B9784: `ブブ    $$フt`
- 0x3B9814: `ブブ  $ $$込0込[?100]`
- 0x3B98A0: `ブブ    $Eけべ  `
- 0x3B98F4: `ブブ  $ $9の ぐ `
- 0x3B9948: `ブブ  $ $<べ0べぐ`
- 0x3B9980: `ブブ    $>0べけべ`
- 0x3B999C: `ブブ  $ $>のべぐべ`
- 0x3B99B8: `ブブ  $ $?べべ  `
- 0x3B9A10: `ブブ    $Eけべ  `
- 0x3B9A80: `ブブ    $9の ぐ `
- 0x3B9AD4: `ブブ  $ $<べ0べぐ`
- 0x3B9B0C: `ブブ    $>0べけべ`
- 0x3B9B28: `ブブ  $ $>のべぐべ`
- 0x3B9B44: `ブブ  $ $?べべ  `
- 0x3B9BF0: `ブブ    $Eけべ  `
- 0x3B9C44: `ブブ  $ $9の ぐ `
- 0x3B9C98: `ブブ  $ $<べ0べぐ`
- 0x3B9CD0: `ブブ    $>0べ8べ`
- 0x3B9CEC: `ブブ  $ $>[?104]べ  `
- 0x3B9D08: `ブブ    $>のべぐべ`
- 0x3B9D24: `ブブ  $ $?べべ  `
- 0x3B9DD0: `ブブ    $Eけべ  `
- 0x3B9E40: `ブブ    $9の ぐ `
- 0x3B9E94: `ブブ  $ $<べ0べぐ`
- 0x3B9ECC: `ブブ    $>0べ8べ`
- 0x3B9EE8: `ブブ  $ $>[?104]べ  `
- 0x3B9F04: `ブブ    $>のべぐべ`
- 0x3B9F20: `ブブ  $ $?べべ  `
- 0x3BA000: `ブブ      $$ゅぷ`
- 0x3BA05C: `ブブ    $Eけべ  `
- 0x3BA078: `ブブ    $E腕べ  `
- 0x3BA0CC: `ブブ  $ $9の 王 `
- 0x3BA0E8: `ブブ  $ $9上 初 `
- 0x3BA13C: `ブブ  $ $<看0看ぐ`
- 0x3BA174: `ブブ    $>0べけべ`
- 0x3BA190: `ブブ  $ $>のべ王べ`
- 0x3BA1AC: `ブブ  $ $>上べ多べ`
- 0x3BA1C8: `ブブ  $ $?看べ  `
- 0x3BA23C: `ブブ    $Eけべ  `
- 0x3BA258: `ブブ    $E腕べ  `
- 0x3BA2AC: `ブブ  $ $9の る `
- 0x3BA2C8: `ブブ  $ $9ミ 王 `
- 0x3BA2E4: `ブブ  $ $9上 初 `
- 0x3BA338: `ブブ  $ $<看0看ぐ`
- 0x3BA370: `ブブ    $>0べけべ`
- 0x3BA38C: `ブブ  $ $>のべ王べ`
- 0x3BA3A8: `ブブ  $ $>上べ初べ`
- 0x3BA3C4: `ブブ  $ $?看べ  `
- 0x3BA3E0: `ブブ    $@だ`
- 0x3BA3FC: `ブブ    $Aク`
- 0x3BA418: `ブブ    $eゅ`
- 0x3BA48C: `ブブ    $Eけべ  `
- 0x3BA4A8: `ブブ    $E腕べ  `
- 0x3BA4FC: `ブブ  $ $9の 王 `
- 0x3BA518: `ブブ  $ $9上 初 `
- 0x3BA56C: `ブブ  $ $<看0看ぐ`
- 0x3BA5A4: `ブブ    $>0べけべ`
- 0x3BA5C0: `ブブ  $ $>のべるべ`
- 0x3BA5DC: `ブブ  $ $>ミべ王べ`
- 0x3BA5F8: `ブブ  $ $>上べ初べ`
- 0x3BA614: `ブブ  $ $?看べ  `
- 0x3BA630: `ブブ    $Bだべ  `
- 0x3BA64C: `ブブ    $Cクべ  `
- 0x3BA668: `ブブ    $hゅぷ  `
- 0x3BA6DC: `ブブ    $Eけべ  `
- 0x3BA6F8: `ブブ    $E腕べ  `
- 0x3BA74C: `ブブ  $ $9の る `
- 0x3BA768: `ブブ  $ $9ミ 王 `
- 0x3BA784: `ブブ  $ $9上 初 `
- 0x3BA7D8: `ブブ  $ $<看0看ぐ`
- 0x3BA810: `ブブ    $>0べけべ`
- 0x3BA82C: `ブブ  $ $>のべるべ`
- 0x3BA848: `ブブ  $ $>ミべ王べ`
- 0x3BA864: `ブブ  $ $>上べ初べ`
- 0x3BA880: `ブブ  $ $?看べ  `
- 0x3BA89C: `ブブ    $@だ`
- 0x3BA8B8: `ブブ    $Aク`
- 0x3BA8D4: `ブブ    $Bだべ  `
- 0x3BA8F0: `ブブ    $Cクべ  `
- 0x3BA90C: `ブブ    $eゅ`
- 0x3BA928: `ブブ !  $hゅぷ  `
- 0x3BA960: `ブブ      $$鉄ぷ`
- 0x3BA9A0: `ブブ    $Eだべ  `
- 0x3BA9F4: `ブブ  $ $9ゅ タ `
- 0x3BAA48: `ブブ  $ $<ミ0ミぐ`
- 0x3BAA80: `ブブ    $>0べるべ`
- 0x3BAA9C: `ブブ  $ $>ゅべタべ`
- 0x3BAAB8: `ブブ  $ $?ミべ  `
- 0x3BAB10: `ブブ    $Eだべ  `
- 0x3BAB64: `ブブ  $ $9す る `
- 0x3BAB80: `ブブ  $ $9ゅ タ `
- 0x3BABD4: `ブブ  $ $<ミ0ミぐ`
- 0x3BAC0C: `ブブ    $>0べるべ`
- 0x3BAC28: `ブブ  $ $>ゅべタべ`
- 0x3BAC44: `ブブ  $ $?ミべ  `
- 0x3BAC7C: `ブブ    $A[?100]`
- 0x3BACF0: `ブブ    $Eだべ  `
- 0x3BAD44: `ブブ  $ $9ゅ タ `
- 0x3BAD98: `ブブ  $ $<ミ0ミぐ`
- 0x3BADD0: `ブブ    $>0べTべ`
- 0x3BADEC: `ブブ  $ $>すべるべ`
- 0x3BAE08: `ブブ  $ $>ゅべタべ`
- 0x3BAE24: `ブブ  $ $?ミべ  `
- 0x3BAE5C: `ブブ    $C[?100]べ  `
- 0x3BAED0: `ブブ    $Eだべ  `
- 0x3BAF24: `ブブ  $ $9す る `
- 0x3BAF40: `ブブ  $ $9ゅ タ `
- 0x3BAF94: `ブブ  $ $<ミ0ミぐ`
- 0x3BAFCC: `ブブ    $>0べTべ`
- 0x3BAFE8: `ブブ  $ $>すべるべ`
- 0x3BB004: `ブブ  $ $>ゅべタべ`
- 0x3BB020: `ブブ  $ $?ミべ  `
- 0x3BB058: `ブブ    $A[?100]`
- 0x3BB090: `ブブ    $C[?100]べ  `
- 0x3BB100: `ブブ      $$ヨぷ`
- 0x3BB194: `ブブ    $$べT`
- 0x3BB358: `ブブ    0ウ[?98]   `
- 0x3BB8C4: `ブブ    $$フt`
- 0x3BB900: `ブブ    $Eだべ  `
- 0x3BB954: `ブブ  $ $9ゅ タ `
- 0x3BB9A8: `ブブ  $ $<ミ0ミぐ`
- 0x3BB9E0: `ブブ    $>0べるべ`
- 0x3BB9FC: `ブブ  $ $>ゅべタべ`
- 0x3BBA18: `ブブ  $ $?ミべ  `
- 0x3BBA50: `ブブ      $$ヨぷ`
- 0x3BBBFC: `ブブ    $>0ちタち`
- 0x3BBC34: `ブブ    $$フな`
- 0x3BBEB4: `ブブ    $$ぷH`
- 0x3BBF0C: `ブブ  $ $9べ エ `
- 0x3BBF60: `ブブ  $ $<ト0トぐ`
- 0x3BBF98: `ブブ    $>0べむべ`
- 0x3BBFB4: `ブブ  $ $>べべエべ`
- 0x3BBFD0: `ブブ  $ $?トべ  `
- 0x3BC008: `ブブ    $Eぐべ  `
- 0x3BC07C: `ブブ  $ $9お む `
- 0x3BC098: `ブブ  $ $9べ エ `
- 0x3BC0EC: `ブブ  $ $<ト0トぐ`
- 0x3BC124: `ブブ    $>0べむべ`
- 0x3BC140: `ブブ  $ $>べべエべ`
- 0x3BC15C: `ブブ  $ $?トべ  `
- 0x3BC1CC: `ブブ    $Eぐべ  `
- 0x3BC25C: `ブブ  $ $9べ エ `
- 0x3BC2B0: `ブブ  $ $<ト0トぐ`
- 0x3BC2E8: `ブブ    $>0べLべ`
- 0x3BC304: `ブブ  $ $>おべむべ`
- 0x3BC320: `ブブ  $ $>べべエべ`
- 0x3BC33C: `ブブ  $ $?トべ  `
- 0x3BC3AC: `ブブ    $Eぐべ  `
- 0x3BC43C: `ブブ  $ $9お む `
- 0x3BC458: `ブブ  $ $9べ エ `
- 0x3BC4AC: `ブブ  $ $<ト0トぐ`
- 0x3BC4E4: `ブブ    $>0べLべ`
- 0x3BC500: `ブブ  $ $>おべむべ`
- 0x3BC51C: `ブブ  $ $>べべエべ`
- 0x3BC538: `ブブ  $ $?トべ  `
- 0x3BC5E0: `ブブ    $Eぐべ  `
- 0x3BC650: `ブブ      %%ハゃ`
- 0x3BC754: `ブブ    $$ぷG`
- 0x3BD6E8: `    !ボ属呪`
- 0x3BD738: `    !ボ属呪`
- 0x3BD788: `    !ボ属呪`
- 0x3C0D38: `    ベ!  ブベ`
- 0x3C0DA8: `     ブ!  ベ ブブ`
- 0x3C2090: `ベプペョ    威`
- 0x3C2F30: `     覚 仲 覚`
- 0x3C2F48: ` 仲!覚 [?476]N  味 `
- 0x3C2F70: ` 鑑 異 鑑 異`
- 0x3C2F84: `!鑑 噂O  持 `
- 0x3C2FA8: ` 殿 解 殿 解!解!殿 彼P  使 `
- 0x3C2FE0: ` [?681] 功 [?681] 功`
- 0x3C2FF4: `![?681] 対Q  稼 `
- 0x3C81F8: ` [?96] [?96] [?97] [?97] [?98] [?98]`
- 0x3C82C8: ` う う え え`
- 0x3C8350: ` す す せ せ そ そ た た`
- 0x3CC114: `ブブ  $ !$ち0ち8`
- 0x3CC448: `ブブ  $ !$[?96]0[?96]だ`
- 0x3CC480: `ブブ    !&0ゅpゅ`
- 0x3CC49C: `ブブ  $ !'[?96]ゅ  `
- 0x3CC4F0: `ブブ      ,$[?96][?192]`
- 0x3CC568: `ブブ     eつ`
- 0x3CC584: `ブブ     fじ`
- 0x3CC5A0: `ブブ     gキ`
- 0x3CC5BC: `ブブ     hレ`
- 0x3CC69C: `ブブ    !$ブ0ブ8`
- 0x3CC744: `ブブ    ,$ビL`
- 0x3CCA94: `ブブ  $ !# [?101] け`
- 0x3CCACC: `ブブ    !&0のべの`
- 0x3CCB74: `ブブ    ,$[?192]へ`
- 0x3CCDF0: `ブブ    !Dの|ミ|`
- 0x3CCFCC: `ブブ    !Dの\ミ\`
- 0x3CD15C: `ブブ    !Dの\ミ\`
- 0x3CD2EC: `ブブ    !Dの\ミ\`
- 0x3CD47C: `ブブ    !Dの\ミ\`
- 0x3CD60C: `ブブ    !Dの\ミ\`
- 0x3CD6F4: `ブブ    (,[?108][?96]`
- 0x3CD904: `ブブ     fあ`
- 0x3CD920: `ブブ     gの`
- 0x3CD93C: `ブブ     hぐ`
- 0x3CD990: `ブブ    !$ゅ0ゅ2`
- 0x3CDA40: `ブブ     Kち`
- 0x3CDBC8: `ブブ    !<[?104]`
- 0x3CDC70: `ブブ    !<[?104][?105]  `
- 0x3CDC8C: `ブブ    !<[?104]こ  `
- 0x3CDD18: `ブブ  $ !$ぐ0ぐけ`
- 0x3CDD50: `ブブ    !&0のむの`
- 0x3CDD6C: `ブブ  $ !'ぐの  `
- 0x3CDDA4: `ブブ    ($ぜむ`
- 0x3CDEE4: `ブブ    !Dの|ミ|`
- 0x3CDFC4: `ブブ     Yち`
- 0x3CDFE0: `ブブ    !Cあ`
- 0x3CDFFC: `ブブ    !Dち`
- 0x3CE018: `ブブ  $ !Eべ`
- 0x3CE410: `ブブ  $ !# [?100] [?192]`
- 0x3CE42C: `ブブ  $ !$けHけ[?192]`
- 0x3CE4F0: `ブブ    !&0タ[?104]タ`
- 0x3CE50C: `ブブ  $ !'けタ  `
- 0x3CE560: `ブブ      ,$すト`
- 0x3CE5A0: `ブブ    #[?101]だ`
- 0x3CE824: `ブブ    !2けタ  `
- 0x3CE8CC: `ブブ  $ !# あ [?192]`
- 0x3CE8E8: `ブブ  $ !$ネHネ[?192]`
- 0x3CE9AC: `ブブ    !&0タクタ`
- 0x3CE9C8: `ブブ  $ !'ネタ  `
- 0x3CEB84: `ブブ    $>0べべべ`
- 0x3CEC54: `ブブ  $ $<べ0べぐ`
- 0x3CEC8C: `ブブ    $>0べぐべ`
- 0x3CECA8: `ブブ  $ $?べべ  `
- 0x3CECE0: `ブブ      $$ゅぷ`
- 0x3CED3C: `ブブ  $ $9べ エ `
- 0x3CED90: `ブブ  $ $<ト0トぐ`
- 0x3CEDC8: `ブブ    $>0べむべ`
- 0x3CEDE4: `ブブ  $ $>べべエべ`
- 0x3CEE00: `ブブ  $ $?トべ  `
- 0x3CEE38: `ブブ    $Eぐべ  `
- 0x3CEEAC: `ブブ  $ $9お む `
- 0x3CEEC8: `ブブ  $ $9べ エ `
- 0x3CEF1C: `ブブ  $ $<ト0トぐ`
- 0x3CEF54: `ブブ    $>0べむべ`
- 0x3CEF70: `ブブ  $ $>べべエべ`
- 0x3CEF8C: `ブブ  $ $?トべ  `
- 0x3CEFFC: `ブブ    $Eぐべ  `
- 0x3CF08C: `ブブ  $ $9べ エ `
- 0x3CF0E0: `ブブ  $ $<ト0トぐ`
- 0x3CF118: `ブブ    $>0べLべ`
- 0x3CF134: `ブブ  $ $>おべむべ`
- 0x3CF150: `ブブ  $ $>べべエべ`
- 0x3CF16C: `ブブ  $ $?トべ  `
- 0x3CF1DC: `ブブ    $Eぐべ  `
- 0x3CF26C: `ブブ  $ $9お む `
- 0x3CF288: `ブブ  $ $9べ エ `
- 0x3CF2DC: `ブブ  $ $<ト0トぐ`
- 0x3CF314: `ブブ    $>0べLべ`
- 0x3CF330: `ブブ  $ $>おべむべ`
- 0x3CF34C: `ブブ  $ $>べべエべ`
- 0x3CF368: `ブブ  $ $?トべ  `
- 0x3CF410: `ブブ    $Eぐべ  `
- 0x3CF480: `ブブ      %%ハゃ`
- 0x3CF514: `ブブ  $ $<べ0べぐ`
- 0x3CF54C: `ブブ    $>0べぐべ`
- 0x3CF568: `ブブ  $ $?べべ  `
- 0x3CF5DC: `ブブ  $ $9お ぐ `
- 0x3CF630: `ブブ  $ $<べ0べぐ`
- 0x3CF668: `ブブ    $>0べぐべ`
- 0x3CF684: `ブブ  $ $?べべ  `
- 0x3CF784: `ブブ  $ $<べ0べぐ`
- 0x3CF7BC: `ブブ    $>0べLべ`
- 0x3CF7D8: `ブブ  $ $>おべぐべ`
- 0x3CF7F4: `ブブ  $ $?べべ  `
- 0x3CF8BC: `ブブ  $ $9お ぐ `
- 0x3CF910: `ブブ  $ $<べ0べぐ`
- 0x3CF948: `ブブ    $>0べLべ`
- 0x3CF964: `ブブ  $ $>おべぐべ`
- 0x3CF980: `ブブ  $ $?べべ  `
- 0x3CFA60: `ブブ      %%ぽゃ`
- 0x3CFB2C: `ブブ    $&0あ`あ`
- 0x3CFC84: `ブブ    $!じ 顔 `
- 0x3CFCD8: `ブブ  $ $$込0込す`
- 0x3CFD10: `ブブ      ((中お`
- 0x3D67A2: ` ブ憶ち 憶  `
- 0x3DC7C6: `i j鎧j同j園j`
- 0x3DE0A0: `ベベベベベベベベベベ`
- 0x3DE0C0: `族族族族族族族族族族`
- 0x3DF4F6: `5タ6ゾ6上6血6幸6俺6`
- 0x3F0896: `     時H顔H看H街H`

