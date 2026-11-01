import ctypes as C,sys,pathlib,json,time,argparse
ROOT=pathlib.Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--core',required=True);parser.add_argument('--save-dir',required=True);parser.add_argument('--restart',action='store_true');parser.add_argument('--appearance',action='store_true');parser.add_argument('--backup',action='store_true');args=parser.parse_args()
OUTPUT=ROOT/'validation';OUTPUT.mkdir(exist_ok=True)
from PIL import Image
core=C.CDLL(str(pathlib.Path(args.core).resolve()))
class Var(C.Structure):_fields_=[('key',C.c_char_p),('value',C.c_char_p)]
class Game(C.Structure):_fields_=[('path',C.c_char_p),('data',C.c_void_p),('size',C.c_size_t),('meta',C.c_char_p)]
ENV=C.CFUNCTYPE(C.c_bool,C.c_uint,C.c_void_p);VIDEO=C.CFUNCTYPE(None,C.c_void_p,C.c_uint,C.c_uint,C.c_size_t);AUDIO=C.CFUNCTYPE(C.c_size_t,C.c_void_p,C.c_size_t);POLL=C.CFUNCTYPE(None);INPUT=C.CFUNCTYPE(C.c_int16,C.c_uint,C.c_uint,C.c_uint,C.c_uint)
options={};strings=[];frame=None;pixel_format=0;pressed=set();pointer=None
@ENV
def env(cmd,data):
 global pixel_format
 if cmd==10:pixel_format=C.cast(data,C.POINTER(C.c_int))[0];return True
 if cmd==15:
  v=C.cast(data,C.POINTER(Var)).contents;value=options.get(v.key)
  if value:v.value=value;return True
  return False
 if cmd==17:C.cast(data,C.POINTER(C.c_bool))[0]=False;return True
 if cmd in [9,31]:
  s=str(pathlib.Path(args.save_dir).resolve()).encode();strings.append(s);C.cast(data,C.POINTER(C.c_char_p))[0]=s;return True
 if cmd==16:
  v=C.cast(data,C.POINTER(Var));i=0
  while v[i].key:
   options[v[i].key]=v[i].value.split(b'; ',1)[1].split(b'|')[0];i+=1
  options[b'melonds_console_mode']=b'DS';options[b'melonds_boot_directly']=b'enabled';options[b'melonds_boot_mode']=b'direct';options[b'melonds_touch_mode']=b'Touch';options[b'melonds_jit_enable']=b'disabled';return True
 if cmd in [10,18,11,1,6,8,32,37]:return True
 if cmd==3:C.cast(data,C.POINTER(C.c_bool))[0]=True;return True
 return False
@VIDEO
def video(data,w,h,pitch):
 global frame
 if data:frame=(C.string_at(data,pitch*h),w,h,pitch)
@AUDIO
def audio(data,n):return n
@POLL
def poll():pass
@INPUT
def inp(port,device,index,key):
 if device==1:return int(key in pressed)
 if device==6 and pointer:
  if key==2:return 1
  if key==0:return int(pointer[0]/256*65535-32768)
  if key==1:return int((pointer[1]+192)/384*65535-32768)
 return 0
pathlib.Path(args.save_dir).mkdir(exist_ok=True)
for name,fn in [('environment',env),('video_refresh',video),('audio_sample_batch',audio),('input_poll',poll),('input_state',inp)]:getattr(core,'retro_set_'+name)(fn)
core.retro_init();core.retro_load_game.argtypes=[C.POINTER(Game)];core.retro_load_game.restype=C.c_bool
rom=(ROOT/'mii-ds.nds').resolve();blob=C.create_string_buffer(rom.read_bytes());game=Game(str(rom).encode(),C.cast(blob,C.c_void_p),len(blob)-1,None)
assert core.retro_load_game(C.byref(game)), 'melonDS rejected ROM'
core.retro_get_memory_data.argtypes=[C.c_uint];core.retro_get_memory_data.restype=C.c_void_p
ram=core.retro_get_memory_data(2)
assert ram, 'Core did not start an emulated console'
# Standard libretro frontend SRAM persistence; guest RAM is never modified.
core.retro_get_memory_size.argtypes=[C.c_uint];core.retro_get_memory_size.restype=C.c_size_t
sram=core.retro_get_memory_data(0);sram_size=core.retro_get_memory_size(0)
sram_file=pathlib.Path(args.save_dir)/'frontend-cartridge.sav'
if sram and sram_size and sram_file.exists():
 saved=sram_file.read_bytes();assert len(saved)==sram_size;C.memmove(sram,saved,sram_size)
if args.restart and sram:assert sram_file.exists(), 'Missing frontend cartridge save' 
def run(n):
 for _ in range(n):core.retro_run()
def capture(name):
 raw,w,h,pitch=frame
 if pixel_format==1:im=Image.frombytes('RGB',(w,h),raw,'raw','BGRX',pitch)
 else:
  im=Image.new('RGB',(w,h));pix=im.load()
  for y in range(h):
   for x in range(w):
    p=2*x+y*pitch;v=raw[p]|raw[p+1]<<8;pix[x,y]=((v>>11)*255//31,((v>>5)&63)*255//63,(v&31)*255//31)
 im.save(OUTPUT/(name+'.png'));print('capture',name,w,h,flush=True)
symbols=json.loads((OUTPUT/'symbols.json').read_text())
def mem(s,n=4):return C.string_at(ram+symbols[s]-0x02000000,n)
def tap(x,y,wait=40):
 global pointer
 pointer=(x,y);run(3);pointer=None;run(wait)
def key(k,wait=40):
 global pressed
 pressed={k};run(2);pressed=set();run(wait)
def avatar():return mem('editor',272)[4:130]
def value(f):return avatar()[64+f]
def scene():return int.from_bytes(mem('screen'),'little')
run(300)
if args.backup:
 if args.restart:parser.error('--backup requires its own fresh save directory, not --restart')
 def backup_message():
  pointer=int.from_bytes(mem('backup_notice'),'little')
  return C.string_at(ram+pointer-0x02000000,96).split(b'\0')[0]
 assert scene()==0
 key(2);assert scene()==9
 original=mem('gallery',12716)
 key(8);assert backup_message()==b'SD card is unavailable.' and mem('gallery',12716)==original
 capture('melonds-backup-missing-sd')
 tap(128,127);assert scene()==0
 tap(140,80,180);tap(80,98,180);assert scene()==1
 key(2,120);assert scene()==3
 draft=avatar();original=mem('gallery',12716)
 key(1);assert scene()==9
 tap(128,87);assert backup_message()==b'Save your draft before backup.'
 assert avatar()==draft and mem('gallery',12716)==original
 capture('melonds-backup-dirty-draft')
 key(0);assert scene()==3
 key(3,300);assert mem('gallery',100)[0]==1
 key(1);assert scene()==9
 original=mem('gallery',12716)
 key(8);assert backup_message()==b'SD card is unavailable.'
 assert avatar()==draft and mem('gallery',12716)==original
 capture('melonds-backup-saved-gallery')
 key(0);assert scene()==3
 if not sram:time.sleep(3.1);run(3)
 if sram and sram_size:sram_file.write_bytes(C.string_at(core.retro_get_memory_data(0),sram_size))
 core.retro_unload_game();core.retro_deinit()
 print('PASS: backup panel buttons/touch, missing-SD errors, dirty-draft guard and unchanged saved gallery',flush=True)
 raise SystemExit(0)
if args.restart:
 tap(100,25,300);tap(42,70,300);key(8,180)
else:
 tap(140,80,180);assert scene()==4;capture('melonds-create-gender')
 tap(80,98,180);assert scene()==1 and value(51)==1
key(2,120);assert scene()==3
if not args.restart:
 tap(80,29);assert int.from_bytes(mem('profile'),'little')==1
 for _ in range(3):key(9,10)
 for x,y in [(116,84),(68,84),(56,106),(116,84),(176,129),(188,84),(188,84)]:tap(x,y,10)
 capture('melonds-nickname-keyboard');tap(192,179,100)
 assert avatar()[:32].split(b'\0')[0]==b'TESTMII'
 tap(175,152)
 for x,y in [(80,129),(212,84),(80,106),(68,84),(56,129)]:tap(x,y,10)
 tap(192,179,100)
 tap(203,29);assert value(46)==1
 tap(62,70);tap(176,98,180);assert value(0)==1
 tap(62,111);tap(48,110,180);assert value(45)==6
 tap(52,152);tap(92,62,10)
 for _ in range(28):tap(164,62,7)
 capture('melonds-original-birthday-font');tap(192,179)
 assert value(49)==2 and value(50)==29
 tap(186,70);tap(128,147);assert value(47)==0
 tap(186,111);tap(128,147);assert value(48)==0
 capture('melonds-profile-settings');key(3,300)
 status=int.from_bytes(mem('editor',272)[268:272],'little')
 assert C.string_at(ram+status-0x02000000,64).split(b'\0')[0]==b'ROM save written'
 key(0,120);assert scene()==1
 for x,y,field in [(128,11,34),(128,32,35),(77,32,39),(77,11,30)]:
  tap(15,137);assert scene()==5
  tap(x,y,120);assert scene()==1 and int.from_bytes(mem('editor',272)[260:264],'little')==field
 capture('melonds-accessory-editor')
 tap(15,34);tap(101,38,150);assert value(5)==1
 key(0);assert int.from_bytes(mem('editor',272)[264:268],'little')!=0;capture('melonds-original-confirmation')
 tap(128,127);assert value(5)==1 and int.from_bytes(mem('editor',272)[264:268],'little')==0
 key(0);tap(128,87,120);assert scene()==0
 tap(100,25,220);tap(42,70,100);key(1,80)
 assert mem('gallery',100)[1]==0
 status=int.from_bytes(mem('editor',272)[268:272],'little')
 assert C.string_at(ram+status-0x02000000,64).split(b'\0')[0]==b'Copying is not allowed.'
 key(8,120);key(2,80);tap(186,111);tap(128,107);key(3,240)
 key(0,80);key(0,80);assert scene()==0
 tap(100,25,220);tap(42,70,100);key(1,150)
 assert mem('gallery',100)[1]==1
 assert mem('gallery',12716)[100+126+64+51]==0 and mem('gallery',12716)[100+126+64+46]==0
 capture('melonds-gallery-copy')
 key(9,60);tap(128,87,220);assert mem('gallery',100)[1]==0 and mem('gallery',100)[0]==1
 print('PASS: original gender/profile/accessory dialogs, keyboard/date/permissions, save, touch discard/cancel, copy permission and transactional copy/delete',flush=True)
else:
 assert avatar()[:32].split(b'\0')[0]==b'TESTMII'
 assert avatar()[32:64].split(b'\0')[0]==b'CODEX'
 assert [value(f) for f in [0,45,46,47,48,49,50,51]]==[1,6,1,0,1,2,29,1]
 capture('melonds-profile-cold-reload')
 print('PASS: cold restart restores name, creator, female body, shirt, favorite, permissions, birthday and Personal Mii flag',flush=True)
if not sram:time.sleep(3.1);run(3)
if sram and sram_size:sram_file.write_bytes(C.string_at(core.retro_get_memory_data(0),sram_size))
core.retro_unload_game();core.retro_deinit()
