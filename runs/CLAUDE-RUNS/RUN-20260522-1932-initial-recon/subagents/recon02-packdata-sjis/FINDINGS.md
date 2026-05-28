# PACKDATA.DIG Shift-JIS Scan -- Findings

## Executive Summary

**PACKDATA.DIG does NOT contain plaintext Shift-JIS text.** The 839MB file consists of binary game assets (3D models, textures, vertex data, etc.). All apparent SJIS matches are false positives from binary data.

The PS2 executable **SLPM_653.78** (4MB) DOES contain ~200 genuine Shift-JIS strings, but these are developer debug messages and system strings, not player-facing game text (dialogue, item names, spell descriptions).

## Methodology

1. **Brute-force SJIS scan (v1-v3)**: Scanned all 839MB of PACKDATA.DIG in 16MB chunks with progressively stricter filters. Even with strict kana-run requirements, returned hundreds of thousands of false positives from binary data that coincidentally matches SJIS byte patterns.

2. **Targeted word search**: Searched for specific SJIS-encoded Japanese words common in RPGs:
   - `desu` (です), `masu` (ます), `kougeki` (攻撃), `mahou` (魔法), `item` (アイテム), `senshi` (戦士), `buki` (武器)
   - Result: Zero hits for game terms. 15 hits for `desu` were all the same data block repeated at ~6.8MB intervals in the 596-601MB region -- binary data, not text.

3. **Context analysis**: Examined raw hex around all matches. Particle byte sequences (は, の, を) were embedded in floating-point numerical data (3D coordinates). No actual text context found.

4. **Executable scan**: Scanned SLPM_653.78 and found 873 SJIS string candidates, of which ~200 are genuine Japanese text.

## What PACKDATA.DIG Contains (Binary Analysis)

- Predominantly binary data: 3D vertex data (floating-point coordinates), texture data, model data
- The data has repeating structural patterns at regular intervals, consistent with packed game assets
- No plaintext strings of any encoding (ASCII, SJIS, EUC-JP, UTF-8) were found
- Text data for this game is likely **compressed**, **encrypted**, or stored in a **custom format** within PACKDATA.DIG's sub-archives

## Executable (SLPM_653.78) Text Findings

Found ~200 genuine SJIS strings at offsets 0x3EC910-0x3FC7F0. These are all **debug/development strings**, not player-facing text:

### Categories found:

1. **Debug battle messages** (offset 0x3EC910-0x3EC960):
   - `デバックチェック！！！！！` (Debug check!!!!!)
   - `デバック戦闘だよ！！！！！` (It's a debug battle!!!!!)
   - `デバック戦闘確認！！！！！` (Debug battle confirmed!!!!!)

2. **Allied Action (アレイド) system** (0x3EE9D0-0x3F3470) -- ~120 strings:
   - Formation break notifications: `フロントガードブレイク`, `マジックシェルブレイク`
   - Allied skill names: `Ｗスラッシュ`, `スタンスマッシュ`, `ホールドアタック`, `ラッシュ`, `ゲイルスラッシュ`, `セイクリッドクロス`, `ソウルクラッシュ`, `ナイトメアクエイク`, `居合斬月斬`, `ダブルブレス`
   - Magic actions: `魔法速射`, `魔法協力`, `マジックウエポン`, `マジックキャンセル`
   - Tactical formations: `散開隊形`, `密集隊形`, `牽制射撃`, `援護射撃`
   - Debug output: `効果レベル = %d`, `ディスペル成功！`, `ディスペル失敗！`

3. **System/error messages** (0x3F3630-0x3FC7F0):
   - `壁イベントデータ作成エラー` (Wall event data creation error)
   - `コールバッファオーバーです！！` (Call buffer overflow!!)
   - `メモリ足りんで〜！！` (Not enough memory~~!!)
   - `アイテム数足りんで〜！！` (Not enough items~~!!)
   - `ガーディアン戦闘！！` (Guardian battle!!)
   - `コンティニューロード！` (Continue load!)
   - `取り付ける人がいないよ。` (There's nobody to equip it to.)

4. **Save data labels** (0x3F9370-0x3FC790):
   - `ＢＵＳＩＮ０中断データ` (BUSIN 0 suspend data)
   - `ＢＵＳＩＮ０データ１/２/３` (BUSIN 0 data 1/2/3)

5. **Developer easter egg** (0x3FC7F0):
   - `松野ゲー起動！！` (Matsuno game startup!!) -- likely a reference to Yasumi Matsuno

## Key Implication for Translation

**The actual translatable game text (dialogue, item names, spell names, UI labels) is NOT stored as plaintext Shift-JIS in PACKDATA.DIG.** It is almost certainly:

1. **Compressed** within PACKDATA.DIG's internal sub-file structure (PACKDATA.DIG likely has an index/directory structure that references compressed blocks)
2. Possibly in **TEMP1.LZH** (334MB, the `.LZH` extension explicitly indicates LHA compression)
3. Possibly in **BSN2_0.DSI** (63MB), though our word search found zero SJIS hits there either

### Recommended Next Steps

1. **Reverse-engineer PACKDATA.DIG's container format**: Look for a file table/index at the beginning or end of the file. The executable references `\PACKDATA.DIG;1` which is a standard PS2 ISO path.
2. **Decompress TEMP1.LZH**: This is a standard LHA archive and may contain the text resources.
3. **Analyze BSN2_0.DSI**: May use a custom compression or encoding scheme.
4. **Examine the executable's data loading code**: The MIPS code around the debug strings likely contains file I/O routines that reveal how PACKDATA.DIG is structured and decompressed.

## Output Files

- Scan results: `C:\Programmieren\wizardrytranslation\dumps\packdata_sjis_scan.txt`
- Scan script: `C:\Programmieren\wizardrytranslation\tools\scan_packdata_sjis.py`
