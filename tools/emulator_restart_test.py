import ctypes as C,sys,pathlib,json,time,argparse
ROOT=pathlib.Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--core',required=True);parser.add_argument('--save-dir',required=True);args=parser.parse_args()
OUTPUT=ROOT/'validation';OUTPUT.mkdir(exist_ok=True)
from PIL import Image
core=C.CDLL(str(pathlib.Path(args.core).resolve()))
class Var(C.Structure):_fields_=[('key',C.c_char_p),('value',C.c_char_p)]
class Game(C.Structure):_fields_=[('path',C.c_char_p),('data',C.c_void_p),('size',C.c_size_t),('meta',C.c_char_p)]
ENV=C.CFUNCTYPE(C.c_bool,C.c_uint,C.c_void_p);VIDEO=C.CFUNCTYPE(None,C.c_void_p,C.c_uint,C.c_uint,C.c_size_t);AUDIO=C.CFUNCTYPE(C.c_size_t,C.c_void_p,C.c_size_t);POLL=C.CFUNCTYPE(None);INPUT=C.CFUNCTYPE(C.c_int16,C.c_uint,C.c_uint,C.c_uint,C.c_uint)
options={};strings=[];frame=None;pressed=set();pointer=None
@ENV
def env(cmd,data):
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
  options[b'desmume_pointer_type']=b'touch';options[b'desmume_cpu_mode']=b'interpreter';return True
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
rom=(ROOT/'mii-ds.nds').resolve();game=Game(str(rom).encode(),None,0,None)
core.retro_mds_configure_save()
assert core.retro_load_game(C.byref(game)), 'load failed'
core.retro_get_memory_data.argtypes=[C.c_uint];core.retro_get_memory_data.restype=C.c_void_p
ram=core.retro_get_memory_data(2)
def run(n):
 for _ in range(n):core.retro_run()
def capture(name):
 raw,w,h,pitch=frame;im=Image.new('RGB',(w,h));pix=im.load()
 for y in range(h):
  for x in range(w):
   p=2*x+y*pitch;v=raw[p]|raw[p+1]<<8;pix[x,y]=((v>>11)*255//31,((v>>5)&63)*255//63,(v&31)*255//31)
 im.save(OUTPUT/(name+'.png'));print('capture',name,w,h,flush=True)
run(240);capture('emulator-home-menu')
pointer=(100,25);run(3);pointer=None;run(90);capture('emulator-gallery')
pointer=(42,70);run(3);pointer=None;run(90)
pressed={8};run(3);pressed=set();run(90)
# View Mii Characters -> stored slot -> Edit.

# Symbol addresses are generated from this exact ELF; inspect actual emulated state.
import subprocess,re
symbols=json.loads((OUTPUT/'symbols.json').read_text())
def mem(symbol,size):
 addr=symbols.get(symbol)
 if symbol=='m':addr=symbols['editor']+4
 if symbol=='field':addr=symbols['editor']+260
 if symbol=='status':addr=int.from_bytes(C.string_at(ram+symbols['editor']+268-0x02000000,4),'little')
 return C.string_at(ram+addr-0x02000000,size)
# Inspection uses the exact ARM build's symbol map; no guest memory is changed.
print('loaded-avatar',mem('m',126).hex(),flush=True)
assert int.from_bytes(mem('save_ready',4),'little')==1
assert mem('m',126)[64+5]==1, 'saved hair selection did not survive cold restart'
capture('emulator-cold-reload')
print('PASS: cold boot restored hair style 1 from ROM cartridge save',flush=True)
# Camera hardware must never be touched in DS execution mode.
pressed={1};run(3);pressed=set();run(90)
assert mem('status',48).split(b'\0')[0]==b'Camera requires DSi mode'
capture('emulator-ds-camera-gate')
# Editing then changing slots must prompt; cancellation preserves the draft.
pointer=(15,34);run(3);pointer=None;run(90)
pointer=(145,38);run(3);pointer=None;run(90)
assert mem('m',126)[69]==2
pressed={11};run(3);pressed=set();run(90)
base_addr=symbols['editor']-0x02000000
assert int.from_bytes(C.string_at(ram+base_addr+264,4),'little')!=0
assert int.from_bytes(C.string_at(ram+base_addr+256,4),'little')==0
pressed={0};run(3);pressed=set();run(90)
assert mem('m',126)[69]==2
capture('emulator-draft-retained')
print('PASS: DS camera gate and discard-cancel workflow',flush=True)
pointer=(181,49);run(3);pointer=None;run(90)
assert mem('m',126)[70]==1, 'hair color swatch did not apply'
pointer=(15,158);run(3);pointer=None;run(90)
pointer=(200,60);run(3);pointer=None;run(90)
assert int.from_bytes(mem('field',4),'little')==43
assert mem('m',126)[64+43]>100, 'body slider did not update height'
capture('emulator-body-slider')
print('PASS: original color-swatch bounds and body-slider input',flush=True)
# Back from a dirty editor must ask, preserve on cancel, and return on confirm.
pressed={0};run(3);pressed=set();run(90)
assert int.from_bytes(C.string_at(ram+base_addr+264,4),'little')!=0
pressed={0};run(3);pressed=set();run(90)
assert int.from_bytes(mem('screen',4),'little')==1
pressed={0};run(3);pressed=set();run(90)
pressed={8};run(3);pressed=set();run(90)
assert int.from_bytes(mem('screen',4),'little')==0
capture('emulator-home-return')
pointer=(100,120);run(3);pointer=None;run(90)
assert int.from_bytes(mem('screen',4),'little')==6
capture('emulator-import-no-sd')
print('PASS: original home/gallery/editor routes and protected Back navigation',flush=True)

core.retro_unload_game();core.retro_deinit()
