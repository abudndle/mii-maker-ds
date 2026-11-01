#!/usr/bin/env python3
"""Synthetic, asset-free original 3DS CLIM -> DS RGB555 converter tests."""
from pathlib import Path
import importlib.util
import struct
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/'tools'/'convert_original_bclim.py'
spec=importlib.util.spec_from_file_location('mii_bclim',MODULE)
codec=importlib.util.module_from_spec(spec)
spec.loader.exec_module(codec)

def fake_clim(w=8,h=8,fmt=13,pixels=None):
    pw=codec.next_power_of_two(w)
    ph=codec.next_power_of_two(h)
    size=pw*ph*codec.FORMAT_BPP[fmt]//8
    if pixels is None:pixels=bytes(size)
    footer=codec.FOOTER.pack(b'CLIM',0xfeff,0x14,0x02020000,len(pixels)+40,
                             1,0,b'imag',16,w,h,fmt,len(pixels))
    return pixels+footer

class TestOriginalBclim(unittest.TestCase):
    def test_all_nine_source_formats(self):
        for fmt in codec.FORMAT_BPP:
            with self.subTest(format=fmt):
                h,data=codec.decode_bclim(fake_clim(fmt=fmt))
                self.assertEqual(h['format'],fmt)
                self.assertEqual(len(data),128)

    def test_morton8_cover(self):
        values={codec.morton8(x,y) for y in range(8) for x in range(8)}
        self.assertEqual(values,set(range(64)))
        self.assertEqual([codec.morton8(x,y) for x,y in
            ((0,0),(1,0),(0,1),(2,0),(0,2))],[0,1,2,4,8])

    def test_a4_transparency(self):
        pix=bytearray(32)
        n=codec.morton8(3,2)
        pix[n//2]|=0xf<<(4*(n%2))
        _,data=codec.decode_bclim(fake_clim(pixels=bytes(pix)))
        words=struct.unpack('<64H',data)
        self.assertEqual(sum(bool(v&0x8000) for v in words),1)
        self.assertEqual(words[2*8+3],0xffff)

    def test_rgb565_channel_order(self):
        pixels=bytearray(128)
        for x,value in enumerate((0x001f,0x07e0,0xf800)):
            struct.pack_into('<H',pixels,codec.morton8(x,0)*2,value)
        _,data=codec.decode_bclim(fake_clim(fmt=5,pixels=pixels))
        self.assertEqual(struct.unpack_from('<HHH',data,0),(0x801f,0x83e0,0xfc00))

    def test_non_power_of_two_dimensions(self):
        h,data=codec.decode_bclim(fake_clim(w=12,h=18))
        self.assertEqual((h['padded_width'],h['padded_height']),(16,32))
        self.assertEqual(len(data),12*18*2)

    def test_reject_bad_headers(self):
        for data in (b'',b'bad',fake_clim()[:-1],fake_clim().replace(b'CLIM',b'FAKE')):
            with self.subTest(size=len(data)),self.assertRaises(ValueError):
                codec.decode_bclim(data)

    def test_packed_nitrofs_widgets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            src=root/'private'/'Select'/'timg'
            src.mkdir(parents=True)
            (src/'BtnArrow.bclim').write_bytes(fake_clim())
            dst=root/'nitrofiles'/'art'/'Select'
            rows=codec.convert_tree(src,dst)
            payload=(dst/'BtnArrow.bin').read_bytes()
            self.assertEqual(len(rows),1)
            self.assertEqual(struct.unpack_from('<HH',payload),(8,8))
            self.assertEqual(len(payload),4+128)
            self.assertTrue((dst/'_manifest.json').exists())

if __name__=='__main__':unittest.main(verbosity=2)
