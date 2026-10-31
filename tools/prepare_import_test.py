#!/usr/bin/env python3
"""Create deterministic fictional CFSD fixtures for the native test build."""
from pathlib import Path
import argparse,binascii,re
root=Path(__file__).resolve().parents[1];a=argparse.ArgumentParser();a.add_argument('--output',type=Path,default=root/'nitrofiles/test-import');args=a.parse_args();args.output.mkdir(parents=True,exist_ok=True)
raw=bytes(int(x,16) for x in re.findall(r'0x([0-9a-f]{2})',(root/'tests/cfs_fixture.h').read_text()));assert len(raw)==96
(args.output/'00-invalid.cfsd').write_bytes(raw[:95]);(args.output/'02-valid.cfsd').write_bytes(raw)
b=bytearray(raw);b[1]&=254;b[26:46]='ReadOnly'.encode('utf-16-le')+bytes(4);b[94:]=binascii.crc_hqx(b[:94],0).to_bytes(2,'big');(args.output/'01-no-copy.cfsd').write_bytes(b)
print('Prepared fictional import fixtures:',args.output)
