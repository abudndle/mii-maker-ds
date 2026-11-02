#!/usr/bin/env python3
"""Report missing prerequisites for a complete, locally sourced DS ROM build."""
import os
import shutil
import sys
from pathlib import Path


def check(root: Path, sdk: Path, toolchain: Path) -> list[str]:
    missing = []
    paths = {
        'BlocksDS SDK makefiles': sdk / 'sys/default_makefiles/rom_arm9/Makefile',
        'original Mii head resource': root / 'nitrofiles/cfl/CFL_Res.dat',
        'original male body resource': root / 'nitrofiles/models/MaleBody.bin',
        'original female body resource': root / 'nitrofiles/models/FemaleBody.bin',
        'original game banner': root / 'assets/ui/original-icon.gif',
    }
    for label, path in paths.items():
        if not path.is_file():
            missing.append(f'{label}: {path}')
        elif path.is_symlink():
            missing.append(f'{label} must be a regular private file, not a symlink: {path}')
        elif path.stat().st_size == 0:
            missing.append(f'{label} is empty: {path}')
    arm_gcc = [toolchain / 'toolchain/gcc-arm-none-eabi/bin/arm-none-eabi-gcc',
               toolchain / 'bin/arm-none-eabi-gcc']
    if not any(p.is_file() for p in arm_gcc) and shutil.which('arm-none-eabi-gcc') is None:
        missing.append('Wonderful ARM compiler (arm-none-eabi-gcc)')
    for executable in ('make', 'python3'):
        if shutil.which(executable) is None:
            missing.append(f'executable: {executable}')
    if not (root / 'nitrofiles').is_dir():
        missing.append('NitroFS resource directory: nitrofiles/')
    return missing


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    sdk = Path(os.environ.get('BLOCKSDS', '/opt/wonderful/thirdparty/blocksds/core'))
    toolchain = Path(os.environ.get('WONDERFUL_TOOLCHAIN', '/opt/wonderful'))
    missing = check(root, sdk, toolchain)
    if missing:
        print('DS ROM build prerequisites missing:')
        for item in missing:
            print(f'  - {item}')
        print('Provide locally owned original resources and BlocksDS before running make.')
        return 1
    print('DS ROM build prerequisites detected; run tools/check_assets.py and make next.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
