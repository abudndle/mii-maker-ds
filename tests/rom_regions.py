"""Real ROM regression for melonDS NTR/TWL boundary; run after make."""
import pathlib,struct,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from fix_nds_regions import fix,crc16
b=(ROOT/'mii-ds.nds').read_bytes()
u32=lambda o:struct.unpack_from('<I',b,o)[0]
limit=struct.unpack_from('<H',b,0x92)[0]*0x80000
assert limit==u32(0x80)==u32(0x1c0) and limit>=0x80000
assert limit+u32(0x1cc)<=u32(0x1d0)
assert u32(0x1d0)+u32(0x1dc)<=u32(0x210)<=len(b)
assert crc16(b[:0x15e])==struct.unpack_from('<H',b,0x15e)[0]
assert b[0x12]==2 and b[0xc:0x10]==b'MDSD'
arm9=u32(0x20)
assert b[arm9:arm9+8]==struct.pack('<II',0xe7ffdeff,0xe7ffdeff)
assert crc16(b[arm9:arm9+0x4000])==struct.unpack_from('<H',b,0x6c)[0]
assert fix(b)==b, 'Fix must be idempotent'
# The entire embedded filesystem must remain accessible in DS cartridge mode.
fat,size=u32(0x48),u32(0x4c)
assert b[fat+size:fat+size+8]==b'NitroFS!'
for off in range(fat,fat+size,8):
 start,end=struct.unpack_from('<II',b,off);assert 0x8000<=start<=end<=limit
# Reconstruct the previous packed layout, then prove relocation preserves payloads.
first_file_end=max(struct.unpack_from('<II',b,off)[1] for off in range(fat,fat+size,8))
old_start=(first_file_end+0x1ff)&~0x1ff
assert old_start<=limit
old=bytearray(b[:old_start]+b[limit:]);delta=limit-old_start
for off in [0x80,0x1c0,0x1d0,0x210]:struct.pack_into('<I',old,off,u32(off)-delta)
struct.pack_into('<H',old,0x92,0)
corrected=fix(old)
new9=struct.unpack_from('<I',corrected,0x1c0)[0];new7=struct.unpack_from('<I',corrected,0x1d0)[0]
assert corrected[new9:new9+u32(0x1cc)]==b[limit:limit+u32(0x1cc)]
assert corrected[new7:new7+u32(0x1dc)]==b[u32(0x1d0):u32(0x1d0)+u32(0x1dc)]
assert corrected[0x4000:first_file_end]==b[0x4000:first_file_end]
print('PASS: accessible NitroFS, aligned DS/DSi boundary, preserved programs/assets, header CRC and idempotent build')
