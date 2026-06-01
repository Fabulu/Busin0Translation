# Fix: Male/Female Overflow in R38

## Problem
R38 MSG 25 ("Male") and MSG 26 ("Female") overflow their single-glyph slots.
These are gender indicator labels that only have room for 1 character.

## Fix Applied
- MSG 25: "Male" -> "M"
- MSG 26: "Female" -> "F"

## File Modified
- `data/translate_chunks/chunk_r38_fix.json`
