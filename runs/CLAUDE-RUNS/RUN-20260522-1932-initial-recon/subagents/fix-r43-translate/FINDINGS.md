# R43 Translation Findings

## Overview
Resource 43 contains 26 messages for the Bar Luna Light tavern (bartender Gin Barbus).
All 26 messages translated and written to `data/translate_chunks/chunk_r43_fix.json`.

## Message Categories
- **Messages 1-2**: Bartender greetings (with/without active quest)
- **Messages 3-5**: Bulletin board, quest accept, quest history
- **Messages 6-8**: Game introduction and prompts
- **Messages 9-17**: Medal game results (win/lose), cost, practice, medals
- **Messages 18-22**: Prize exchange flow (select, confirm, assign, inventory full)
- **Messages 23-24**: Yes/No options
- **Messages 25-26**: Practice/Game start confirmations

## Decoding Artifacts Found
Several kanji in the source text are decoding artifacts (wrong character substituted):
- `掲鉄板` should be `掲示板` (bulletin board) - msg 3
- `気分転更` should be `気分転換` (change of pace) - msg 6
- `交更` should be `交換` (exchange) - msgs 12, 19
- `錠め` should be `止め` (stop) - msg 14
- `持ち士` should be `持ち物` (belongings) - msg 22

These are font table mapping issues, not translation problems.

## Line Length Compliance
All translations kept within 18 characters per line (between `/` separators).
Longest line: "how'd that job go?" = 18 chars (exactly at limit).

## Tone
Gin Barbus uses casual/rough bartender speech. Translations use contractions
("d'ya", "ya", "wanna", "lemme") to match the informal Japanese register.
