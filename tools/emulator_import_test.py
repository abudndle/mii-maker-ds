import ctypes as C,sys,pathlib,json,time,argparse
ROOT=pathlib.Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--core',required=True);parser.add_argument('--save-dir',required=True);parser.add_argument('--restart',action='store_true');parser.add_argument('--appearance',action='store_true');parser.add_argument('--animation',action='store_true');parser.add_argument('--sliders',action='store_true');parser.add_argument('--image',action='store_true');parser.add_argument('--benchmark',action='store_true');parser.add_argument('--import-no-sd',action='store_true');parser.add_argument('--rom');parser.add_argument('--symbols');args=parser.parse_args()
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
rom=pathlib.Path(args.rom).resolve() if args.rom else (ROOT/'mii-ds.nds').resolve();blob=C.create_string_buffer(rom.read_bytes());game=Game(str(rom).encode(),C.cast(blob,C.c_void_p),len(blob)-1,None)
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
symbols=json.loads(pathlib.Path(args.symbols).read_text()) if args.symbols else json.loads((OUTPUT/'symbols.json').read_text())
def mem(s,n=4):return C.string_at(ram+symbols[s]-0x02000000,n)

def tap(x,y,wait=150):
 global pointer
 pointer=(x,y);run(3);pointer=None;run(wait)
def key(k,wait=150):
 global pressed
 pressed={k};run(3);pressed=set();run(wait)
def scene():return int.from_bytes(mem('screen'),'little')
def draft():return mem('editor',272)[4:130]
run(300)
if args.restart:
 tap(100,25);tap(85,70);key(8)
 assert scene()==1 and draft()[:32].split(b'\0')[0]==b'CodecTest'
 assert draft()[32:64].split(b'\0')[0]==b'DS Test'
 assert [draft()[64+i] for i in [0,5,19,20,21,45,46,47,48,49,50,51]]==[1,84,10,7,14,9,0,1,1,2,29,0]
 assert mem('gallery',12716)[100+2*126+64+51]==1
 capture('melonds-import-cold-reload')
 print('PASS: cold restart restores imported standard Mii appearance/name/permissions and independent local Personal Mii',flush=True)
else:
 tap(100,120);assert scene()==6
 assert int.from_bytes(mem('importer',9708)[9704:9708],'little')==0
 key(8);assert scene()==6 and mem('gallery',100)[0]==0
 capture('melonds-import-invalid-file')
 key(5);assert int.from_bytes(mem('importer',9708)[9704:9708],'little')==1
 key(8,300);assert scene()==2 and mem('gallery',100)[0]==1
 key(8);assert scene()==2
 assert mem('gallery',12716)[100+64+61]==1 and mem('gallery',12716)[100+64+48]==0
 capture('melonds-import-read-only')
 key(0);tap(100,120);key(5);key(5);key(8,300)
 assert scene()==2 and mem('gallery',100)[1]==1
 assert mem('gallery',12716)[100+126:132+126].split(b'\0')[0]==b'CodecTest'
 assert mem('gallery',12716)[100+126+64+46]==0 and mem('gallery',12716)[100+126+64+51]==0
 capture('melonds-import-standard-mii')
 key(0);tap(140,80);tap(80,98)
 assert scene()==1 and draft()[64+51]==1 and draft()[64+46]==1
 key(3,300)
 assert mem('gallery',100)[2]==1
 print('PASS: native fixture-backed import rejects malformed records, retains copy-disabled Miis read-only, decodes original standard fields, transactionally saves and assigns Personal only to first locally created Mii',flush=True)
if sram and sram_size:sram_file.write_bytes(C.string_at(core.retro_get_memory_data(0),sram_size))
core.retro_unload_game();core.retro_deinit()
