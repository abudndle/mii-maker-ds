#!/usr/bin/env python3
"""Original common backdrop for the DS-specific Mii file browser."""
from pathlib import Path
import struct
from PIL import Image
from layouts import render
root=Path(__file__).resolve().parents[1]
p=root/'assets/decoded/layout/EDITCommon.arc.files/blyt/EditBG.bclyt'
im=render(p,multi_texture=True)[0].resize((256,192),Image.Resampling.LANCZOS).convert('RGB')
(root/'nitrofiles/ui/import-bottom.rgb555').write_bytes(b''.join(struct.pack('<H',0x8000|(r>>3)|((g>>3)<<5)|((b>>3)<<10)) for r,g,b in im.get_flattened_data()))
