"""Asset-free original CLAN parser regressions."""
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from clan_keyframes import parse, evaluate


def sample(order="<", kind=b"CLPA", typ=2):
    payload = (struct.pack(order+"fff",0,10,5) + struct.pack(order+"fff",2,20,5)) if typ==2 else (
        struct.pack(order+"fI",0,0) + struct.pack(order+"fI",2,1))
    channel = struct.pack(order+"BBHHHI",0,1,typ,2,0,12) + payload
    tag = kind + bytes([1,0,0,0]) + struct.pack(order+"I",12) + channel
    entry = b"N_BtnTop_00".ljust(20,b"\0") + bytes(4) + struct.pack(order+"I",28) + tag
    pai = b"pai1" + struct.pack(order+"I",24+len(entry)) + struct.pack(order+"HBBHHI",3,0,0,0,1,20) + struct.pack(order+"I",24) + entry
    bom = b"\xff\xfe" if order=="<" else b"\xfe\xff"
    return b"CLAN" + bom + struct.pack(order+"HIIHH",20,0x2020000,20+len(pai),1,0) + pai


class TestClanKeys(unittest.TestCase):
    def test_float_little_endian(self):
        keys=parse(sample())["tracks"][0]["keys"]
        self.assertEqual(keys, [[0.0,10.0,5.0],[2.0,20.0,5.0]])
        self.assertAlmostEqual(evaluate(keys,1),15)
    def test_float_big_endian(self):
        self.assertEqual(parse(sample(">"))["tracks"][0]["keys"][1][1],20)
    def test_visibility_steps(self):
        keys=parse(sample(kind=b"CLVI",typ=1))["tracks"][0]["keys"]
        self.assertEqual(evaluate(keys,1,discrete=True),0)
        self.assertEqual(evaluate(keys,2,discrete=True),1)
    def test_texture_pattern_steps(self):
        self.assertEqual(parse(sample(kind=b"CLTP",typ=1))["tracks"][0]["value_type"],1)
    def test_corrupt_section_length(self):
        payload=bytearray(sample())
        payload[24:28]=struct.pack("<I",0xFFFFFFFF)
        with self.assertRaises(ValueError):parse(payload)
    def test_corrupt_target_offset(self):
        payload=bytearray(sample())
        payload[80:84]=struct.pack("<I",0xFFFFFFFF)
        with self.assertRaises(ValueError):parse(payload)
    def test_nonfinite_key(self):
        payload=bytearray(sample())
        payload[96:100]=struct.pack("<f",float("nan"))
        with self.assertRaises(ValueError):parse(payload)
    def test_duplicate_keys(self):
        self.assertEqual(evaluate([[0,1,0],[1,2,0],[1,3,0]],1),3)
    def test_negative_frames(self):
        self.assertEqual(evaluate([[-10,4,0],[1,9,0]],-12),4)


if __name__ == "__main__":
    unittest.main()
