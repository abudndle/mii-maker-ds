#!/usr/bin/env python3
"""Fail clearly before packing a ROM without the locally supplied resources."""
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
required=['nitrofiles/cfl/CFL_Res.dat','nitrofiles/models/MaleBody.bin','nitrofiles/models/FemaleBody.bin','nitrofiles/models/MaleBody.ani','nitrofiles/models/FemaleBody.ani','nitrofiles/ui/EditBody.rgb555','nitrofiles/ui/home-bottom.rgb555','nitrofiles/ui/profile.rgb555','nitrofiles/font/number.bin','assets/ui/original-icon.gif','source/ui_generated.h','source/ui_hits.h','source/menu_generated.h','source/profile_generated.h','source/ui_font.h']
missing=[p for p in required if not (root/p).is_file()]
if missing:
 print('Required local Mii Maker resources are missing:',file=sys.stderr)
 for p in missing:print('  '+p,file=sys.stderr)
 print('Supply your own extracted resource bundle or regenerate it with the project tools. CFL_DB.dat is not used.',file=sys.stderr)
 sys.exit(1)
