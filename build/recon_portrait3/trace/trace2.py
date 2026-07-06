import sys, struct, json, glob, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'tools'); sys.path.insert(0,'build')
import patch_section1_offsets as P

# load glyph map the way build does
import build_v9  # may run build... no. Instead replicate decode using data files
