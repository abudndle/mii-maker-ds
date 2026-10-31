import ctypes as C,sys,pathlib,json,time,argparse
ROOT=pathlib.Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--core',required=True);parser.add_argument('--save-dir',required=True);parser.add_argument('--restart',action='store_true');parser.add_argument('--appearance',action='store_true');parser.add_argument('--animation',action='store_true');parser.add_argument('--sliders',action='store_true');parser.add_argument('--image',action='store_true');parser.add_argument('--benchmark',action='store_true');parser.add_argument('--import-no-sd',action='store_true');parser.add_argument('--qr-screen',action='store_true');parser.add_argument('--rom');parser.add_argument('--symbols');args=parser.parse_args()
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
run(300);capture('melonds-home')
print('startup',{s:mem(s).hex() for s in ['screen','ok','save_ready']},flush=True)
assert int.from_bytes(mem('ok'),'little')==1, 'NitroFS failed'
assert int.from_bytes(mem('screen'),'little')==0, 'Main menu unavailable'
if args.restart:
 pointer=(100,25);run(3);pointer=None;run(120)
 pointer=(42,70);run(3);pointer=None;run(300)
 pressed={8};run(3);pressed=set();run(120)
else:
 pointer=(140,80);run(3);pointer=None;run(90)
 pointer=(80,98);run(3);pointer=None;run(120)
capture('melonds-editor')
print('editor',mem('screen').hex(),'ready preview modes',mem('preview_ready',12).hex(),flush=True)
assert int.from_bytes(mem('screen'),'little')==1
assert int.from_bytes(mem('preview_ready',12)[4:8],'little')==1
assert all(int.from_bytes(mem('body_sizes',8)[i:i+4],'little')>56 for i in [0,4]), 'Original body resources missing'
if args.benchmark:
 def metrics():return {n:int.from_bytes(mem(n),'little') for n in ['render_ticks','render_completed','render_cancelled_count']}
 before=metrics();run(600);after=metrics();delta={n:after[n]-before[n] for n in before}
 delta['mean_vblanks_per_completed_preview']=delta['render_ticks']/max(1,delta['render_completed'])
 delta['observed_preview_fps']=delta['render_completed']/10
 delta['scope']='Actual DS ARM interpreter execution, 600 VBlanks, original idle portrait; not physical hardware FPS'
 pathlib.Path(args.save_dir,'render-benchmark.json').write_text(json.dumps(delta,indent=2)+'\n')
 print('BENCHMARK',json.dumps(delta),flush=True)
 core.retro_unload_game();core.retro_deinit();sys.exit(0)
if args.restart:
 assert mem('gallery',12716)[100+69]==1, 'Saved hairstyle not restored'
 capture('melonds-cold-reload')
 print('PASS: melonDS cold restart restored saved Mii appearance',flush=True)
else:
 pointer=(15,34);run(3);pointer=None;run(90)
 pointer=(101,38);run(3);pointer=None;run(90)
 assert mem('editor',272)[4+69]==1, 'Original hair choice did not apply'
 pressed={3};run(3);pressed=set();run(240)
 status=int.from_bytes(mem('editor',272)[268:272],'little')
 print('save-status',C.string_at(ram+status-0x02000000,64).split(b'\0')[0],flush=True)
 assert C.string_at(ram+status-0x02000000,64).split(b'\0')[0]==b'ROM save written'
 capture('melonds-after-save')
 print('PASS: melonDS DS direct boot, NitroFS, original head, touch hairstyle and cartridge save',flush=True)
if args.image and not args.restart:
 pressed={0};run(3);pressed=set();run(90)
 pointer=(100,25);run(3);pointer=None;run(120)
 pointer=(42,70);run(3);pointer=None;run(90)
 pressed={2};run(3);pressed=set();run(180)
 status=int.from_bytes(mem('editor',272)[268:272],'little')
 assert C.string_at(ram+status-0x02000000,64).split(b'\0')[0]==b'SD card is unavailable.'
 capture('melonds-image-no-sd')
 pressed={8};run(3);pressed=set();run(120)
 print('PASS: native image-export route reports absent SD without changing cartridge Mii',flush=True)
if args.import_no_sd and not args.restart:
 pressed={0};run(3);pressed=set();run(90)
 pointer=(100,120);run(3);pointer=None;run(180)
 assert int.from_bytes(mem('screen'),'little')==6
 assert int.from_bytes(mem('importer',9708)[9704:9708],'little')==0
 capture('melonds-import-no-sd')
 pressed={8};run(3);pressed=set();run(60)
 assert mem('gallery',100)[1]==0
 pressed={0};run(3);pressed=set();run(60)
 pointer=(100,25);run(3);pointer=None;run(120)
 pointer=(42,70);run(3);pointer=None;run(90)
 pressed={8};run(3);pressed=set();run(120)
 print('PASS: native import browser rejects absent SD and returns without altering gallery',flush=True)
if args.qr_screen and not args.restart:
 pressed={0};run(3);pressed=set();run(90)
 pointer=(100,155);run(3);pointer=None;run(180)
 assert int.from_bytes(mem('screen'),'little')==7
 pressed={8};run(3);pressed=set();run(300)
 assert int.from_bytes(mem('qr_matrix_valid'),'little')==1
 capture('melonds-native-qr')
 pressed={9};run(3);pressed=set();run(90)
 assert int.from_bytes(mem('screen'),'little')==7
 pressed={0};run(3);pressed=set();run(60)
 pointer=(100,25);run(3);pointer=None;run(120)
 pointer=(42,70);run(3);pointer=None;run(90)
 pressed={8};run(3);pressed=set();run(120)
 print('PASS: native QR generation/display and DS camera-scan gate',flush=True)
if args.appearance:
 pointer=(15,75);run(3);pointer=None;run(90)
 pointer=(209,109);run(3);pointer=None;run(90)
 assert mem('editor',272)[4+64+10]==5, 'Eye enlargement button did not apply'
 pointer=(238,84);run(3);pointer=None;run(90)
 assert mem('editor',272)[4+64+12]==4, 'Eye rotation button did not apply'
 pointer=(209,59);run(3);pointer=None;run(90)
 assert mem('editor',272)[4+64+13]==7, 'Eye spacing button did not apply'
 capture('melonds-original-transform-controls')
 pointer=(224,158);run(3);pointer=None;run(90)
 assert mem('editor',272)[4+64+10]==4 and mem('editor',272)[4+64+12]==3
 pointer=(15,158);run(3);pointer=None;run(120);capture('melonds-original-body')
 assert int.from_bytes(mem('preview_ready',12)[8:12],'little')==1, 'Full body renderer did not complete'
 pointer=(200,60);run(3);pointer=None;run(120)
 assert mem('editor',272)[4+64+43]>100, 'Height slider did not apply'
 pointer=(200,126);run(3);pointer=None;run(120)
 assert mem('editor',272)[4+64+44]>100, 'Build slider did not apply'
 capture('melonds-original-body-sliders')
 pressed={5};run(1);pressed=set();run(30)
 pressed={7};run(1);pressed=set();run(120)
 assert mem('editor',272)[4+64+45]==1, 'Shirt color did not apply'
 capture('melonds-original-shirt-color')
 pointer=(15,10);run(3);pointer=None;run(90)
 pointer=(113,11);run(3);pointer=None;run(90)
 assert int.from_bytes(mem('editor',272)[260:264],'little')==4, 'Original makeup subtab did not open'
 pointer=(146,11);run(3);pointer=None;run(90)
 assert int.from_bytes(mem('editor',272)[260:264],'little')==3, 'Original lines subtab did not open'
 pointer=(70,11);run(3);pointer=None;run(90)
 assert int.from_bytes(mem('editor',272)[260:264],'little')==2
 capture('melonds-original-face-tabs')
 print('PASS: actual transform/reset controls, body/sliders/shirt and original face subtabs',flush=True)
if args.sliders:
 pointer=(15,158);run(3);pointer=None;run(180)
 for field,y in [(43,60),(44,126)]:
  pointer=(80,y);run(12)
  observed=[]
  for x in [80,95,110,125,140,155,170,185,200,216]:
   pointer=(x,180);run(5)
   observed.append(mem('editor',272)[4+64+field])
  assert observed==sorted(observed) and len(set(observed))>=8, observed
  assert observed[-1]==127, observed
  pointer=(0,10);run(5);assert mem('editor',272)[4+64+field]==0, 'Captured drag did not clamp left'
  pointer=(255,10);run(5);assert mem('editor',272)[4+64+field]==127, 'Captured drag did not clamp right'
  pointer=None;run(160)
  assert int.from_bytes(mem('slider_field'),'little',signed=True)==-1
  old=mem('editor',272)[4+64+field]
  pointer=(40,180);run(6);pointer=None;run(30)
  assert mem('editor',272)[4+64+field]==old, 'Released drag still changed slider'
 capture('melonds-free-slider-drag')
 print('PASS: native continuous height/build dragging, intermediate values, capture outside track, endpoint clamp and release',flush=True)
if args.animation:
 assert all(int.from_bytes(mem('animations',56)[i:i+4],'little') for i in [0,28]), 'Original animations did not load'
 pointer=(15,158);run(3);pointer=None;run(180)
 before=int.from_bytes(mem('rendered_animation_frames'),'little');snapshot=mem('editor',272)[4:130]
 frames=[];indices=set()
 for _ in range(48):
  run(5);indices.add(int.from_bytes(mem('animation_index'),'little'))
  raw,w,h,pitch=frame
  assert pixel_format==1
  frames.append(Image.frombytes('RGB',(w,h),raw,'raw','BGRX',pitch))
 after=int.from_bytes(mem('rendered_animation_frames'),'little')
 assert after>before+8 and len(indices)>12, (before,after,indices)
 assert mem('editor',272)[4:130]==snapshot, 'Animation changed Mii data'
 assert len({im.crop((0,0,256,192)).tobytes() for im in frames})>8, 'No visible original pose motion'
 frames[0].save(OUTPUT/'melonds-original-idle.gif',save_all=True,append_images=frames[1:],duration=83,loop=0)
 print('PASS: native original idle playback, both animation resources loaded, visible pose changes, Mii data unchanged',flush=True)
if not sram:
 # Older core flushes its own file after a wall-clock debounce.
 time.sleep(3.1);run(3)
if sram and sram_size:
 sram_file.write_bytes(C.string_at(core.retro_get_memory_data(0),sram_size))
core.retro_unload_game();core.retro_deinit()
