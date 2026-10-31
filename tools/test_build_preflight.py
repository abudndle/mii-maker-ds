#!/usr/bin/env python3
"""Portable fixture checks for build prerequisite diagnostics."""
import importlib.util
import tempfile
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('build_preflight', Path(__file__).with_name('build_preflight.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    sdk = root / 'sdk'
    tools = root / 'toolchain'
    needed = [
        sdk / 'sys/default_makefiles/rom_arm9/Makefile',
        tools / 'toolchain/gcc-arm-none-eabi/bin/arm-none-eabi-gcc',
        root / 'nitrofiles/cfl/CFL_Res.dat',
        root / 'nitrofiles/models/MaleBody.bin',
        root / 'nitrofiles/models/FemaleBody.bin',
        root / 'assets/ui/original-icon.gif',
    ]
    with patch.object(module.shutil, 'which', side_effect=lambda name: '/usr/bin/' + name if name in ('make', 'python3') else None):
        missing = module.check(root, sdk, tools)
        assert missing, 'empty environment incorrectly allowed'
        for item in needed:
            item.parent.mkdir(parents=True, exist_ok=True)
            item.write_bytes(b'fixture')
        assert not module.check(root, sdk, tools), 'complete fixture incorrectly rejected'
        needed[2].unlink()
        missing = module.check(root, sdk, tools)
        assert any('head resource' in entry for entry in missing)
        needed[2].write_bytes(b'fixture')
        needed[2].write_bytes(b'')
        assert any('head resource is empty' in entry for entry in module.check(root, sdk, tools))
        needed[2].write_bytes(b'fixture')
        needed[0].unlink()
        assert any('BlocksDS' in entry for entry in module.check(root, sdk, tools))
print('PASS: build prerequisite detection and complete fixture')
