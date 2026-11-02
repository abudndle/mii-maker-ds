# M80 — Private acceptance report

After building from your privately held original resources:

```sh
python3 tools/private_rom_acceptance.py /path/to/MiiMaker_DS_Resources.zip --docker
```

If melonDS is installed, add `--emulator /path/to/melonDS`. The command
writes `build/private-acceptance-report.json` containing SHA-256 digests of
the input archive and built ROM, ROM size, and whether emulator launch was
requested. This report is private build evidence, not proof of game parity.

A successful build must still be followed by real melonDS testing of first-boot
User Mii creation, cartridge save/reload, multi-Mii rooms, touch dragging,
room navigation, editor models, crown/pants semantics, animation, and DSi
camera gating. Never upload proprietary original resources or ROMs to public
GitHub, workflow logs, or public artifacts.
