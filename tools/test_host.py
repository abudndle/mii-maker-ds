#!/usr/bin/env python3
"""Run portable tests without requiring any Nintendo assets."""
from pathlib import Path
import argparse,os,subprocess,tempfile
root=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--cc',default='cc');a.add_argument('--no-sanitizers',action='store_true');args=a.parse_args()
suites={'backup':['avatar','save','save_compact','backup','unicode'],'save_nds_spi':['save_nds'],'saved_select':['saved_select'],'room':['room'],'clan_adjust':['clan_adjust','clan_curve'],'clan_editor':['clan_editor','clan_curve'],'clan_dialog':['clan_dialog','clan_curve'],'clan_visual':['clan_curve','clan_home','clan_overlay'],'clan_curve':['clan_curve'],'clan_home':['clan_home','clan_curve'],'gui_tween':['gui_tween'],'animation_clock':['animation'],'motion':['motion'],'core':['avatar'],'save':['avatar','save'],'save_compact':['avatar','save','save_compact','unicode'],'editor':['avatar','save','editor','unicode'],'profile':['avatar','profile'],'transform':['avatar','transform'],'menu':['menu'],'thumbnail':['thumbnail','avatar'],'view':['view'],'cfl_resource':['cfl_resource'],'image':['image'],'mii_codec':['avatar','unicode','mii_codec'],'exchange':['avatar','unicode','mii_codec','exchange'],'status':['avatar','status'],'save_migration':['avatar','save','save_compact','unicode'],'mii_qr':['avatar','unicode','mii_codec','mii_qr','qr_photo','qr_scan','vendor/aes/aes','vendor/qr/qrcodegen','vendor/quirc/quirc','vendor/quirc/identify','vendor/quirc/decode','vendor/quirc/version_db']}
env=os.environ.copy();env['ASAN_OPTIONS']='detect_leaks=0'
with tempfile.TemporaryDirectory(prefix='mii-ds-tests-') as td:
 for name,modules in suites.items():
  print("RUN:",name,flush=True)
  exe=Path(td)/name
  cmd=[args.cc,'-std=c11','-Wall','-Wextra','-Werror','-g','-I',str(root/'source')]
  # The cartridge-SPI host suite deliberately substitutes the NDS SDK header.
  if name=='save_nds_spi':cmd+=['-I',str(root/'tests'/'mock_nds')]
  if not args.no_sanitizers:cmd+=['-fsanitize=address,undefined']
  cmd += [str(root/'tests'/(name+'.c'))]+[str(root/'source'/(m+'.c')) for m in modules]+['-lm','-o',str(exe)]
  subprocess.run(cmd,check=True)
  import_dir=Path(td)/'import';import_dir.mkdir(exist_ok=True)
  command=[str(exe)]+([str(import_dir)] if name=='backup' else [str(Path(td)/'image.bmp')] if name=='image' else [str(import_dir)] if name=='exchange' else [str(Path(td)/'qr.bin'),str(Path(td)/'qr.png')] if name=='mii_qr' else [])
  subprocess.run(command,check=True,env=env)
print('PASS: all %d asset-free portable suites' % len(suites))
