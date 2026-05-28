#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Translate batch_03 R1203 - Main story resource for Busin 0."""

import json, os

INPUT  = r"C:\Programmieren\wizardrytranslation\data\type2_translation_batches\batch_03_R1203.json"
OUTPUT = r"C:\Programmieren\wizardrytranslation\data\type2_translated\batch_03.json"

with open(INPUT, "r", encoding="utf-8") as f:
    batch = json.load(f)

# Load translations from the tmp file
import sys
sys.path.insert(0, "/tmp")

# Read translations dict from the written file
T = {}
exec_globals = {}
with open("/tmp/translate_b03.py", "r", encoding="utf-8") as f:
    content = f.read()
# Extract just the T dict - easier to just duplicate it here

# Actually let's just run the original script directly
exec(compile(open(r"/tmp/translate_b03.py", "r", encoding="utf-8").read(), "translate_b03.py", "exec"))
