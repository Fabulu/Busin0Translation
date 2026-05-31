# R37 Chargen Prompt Capitalization Fix

## Date: 2026-05-28

## Files Modified

### chunk_r37_r48_r49_translated.json
| Msg | Old | New | Note |
|-----|-----|-----|------|
| 2 | "choose your gender. / " | "Enter your name. / " | Wrong translation + capitalization (JP says name input) |
| 3 | "select gender. / " | "Select gender. / " | Capitalized |
| 4 | "select a race. / " | "Select a race. / " | Capitalized |
| 5 | "select alignment. / " | "Select alignment. / " | Capitalized |
| 6 | "select a class. / " | "Select a class. / " | Capitalized |
| 7 | "allocate stat / points. /" | "Allocate stat / points. /" | Capitalized |

### chunk_r37_extra.json
| Msg | Old | New | Note |
|-----|-----|-----|------|
| 124 | "press o or x to / confirm. / " | "Press O or X to / confirm. / " | Capitalized sentence + button letters |

## Summary
- 7 chargen prompts fixed for capitalization
- Message 2 also had incorrect translation: Japanese says "enter your name" but was translated as "choose your gender"
- All R37 instruction prompts now start with uppercase
