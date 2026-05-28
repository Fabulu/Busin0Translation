# EXE Reverse Engineering Findings

## Text Renderer Architecture

### Key Functions (vaddr → file offset = vaddr - 0x100000 + 0x80)
- `func_302990` (0x302990): Reads 16-bit BE glyph code from MSG data
- `func_3029B0` (0x3029B0): MSG control code dispatcher (FE00-FFF6 range)
- `func_302910` (0x302910): Glyph queue setup, stores to array at 0x565150
- `func_302DB0` (0x302DB0): Glyph render/draw — tracks x($s0), line($s1), charcount($s2)
- `func_303C60` (0x303C60): Main TextEvent renderer (~7000 instructions)
- `func_303510` (0x303510): FontDisp setup, advances data pointer

### Control Codes (CORRECTED)
- 0xFB00-0xFB09: Extended function codes
- 0xFC00-0xFC0A: Text formatting/color codes
- 0xFD00-0xFD27: Special character/icon codes (40 entries)
- 0xFFC0-0xFFC9: Window/display control
- 0xFFCA: Special page/scroll
- 0xFFD0-0xFFD9: Variable insertion codes
- 0xFFE0-0xFFE7: Effect codes
- 0xFFF0-0xFFF6: Variable/number display
- 0xFFFD: LINE BREAK (new line)
- 0xFFFE: PAGE BREAK (clear and continue)
- 0xFFFF: End of message

### 12px Glyph Width
- NOT a simple constant — computed via shift-and-add: (x*2+x)*4 = x*12
- Used for BOTH 12-byte display struct stride AND 12-pixel cell width
- Changing it breaks struct layout
- Font width table at VA 0x2A5E80 IS read but not used for TextEvent rendering
- Game has dormant VWF (variable width font) code path — not active for TextEvent

### Text Box Width Parameters
- Narration box: 140px at file 0x1F3608 (`addiu t1, zero, 140`)
- Small box: 100px at file 0x1F3524
- Created via function at vaddr 0x484FD0, width masked to byte (max 255)

### Hardcoded Glyph Tables in EXE Data Section
- 0x3B3136-0x3B3844: Full available glyph list
- 0x3C3026-0x3C5174: Menu label pair structs
- 0x3C5B32-0x3C6186: Kana mapping table
- 0x3C844A-0x3C8F64: Stat/attribute labels (THE chargen labels!)
- 0x3C93AE-0x3C93D0: NPC names (Emilia, Lute)
- 0x3C99B8-0x3CA6EF: Name entry grid
- 0x3C9DA0-0x3C9DFC: Tab/button bitmap glyph IDs (6400+)
- 0x3DDC48-0x3DDF48: Font width tables (4 × 248 bytes)
- 0x3F9D00-0x3F9EC0: Type suffix table
- All EXE tables use LE uint16 (not BE like MSG files)

### Debug Strings
- 0x4F3D40: "FontDispSetCnt Max Over !!!"
- 0x4F3CA0: "TextEventMsgLinkSetCnt Over !!!!!"
- 0x4FC753: "SysFont Init!!!"
- 0x4F0336: "BattleFontKill"
- 0x4F3452: "FCD_event_font"

### Tools Available
- rabbitizer (pip): MIPS instruction decoder
- spimdisasm (pip): Full MIPS disassembler with R5900 support
- Ghidra + ghidra-emotionengine-reloaded: Full PS2 RE framework
- PCSX2-MCP: AI-powered PS2 debugger (can set memory breakpoints)
- Disassembly scripts in tools/disasm_*.py
