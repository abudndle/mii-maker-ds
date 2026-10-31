#!/usr/bin/env python3
"""Run portable tests without requiring any Nintendo assets."""
from pathlib import Path
import argparse,os,subprocess,tempfile
root=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--cc',default='cc');a.add_argument('--no-sanitizers',action='store_true');args=a.parse_args()
suites={'core':['avatar'],'save':['avatar','save'],'save_compact':['avatar','save','save_compact'],'editor':['avatar','save','editor'],'profile':['avatar','profile'],'transform':['avatar','transform'],'menu':['menu'],'cfl_resource':['cfl_resource'],'image':['image']}
env=os.environ.copy();env['ASAN_OPTIONS']='detect_leaks=0'
with tempfile.TemporaryDirectory(prefix='mii-ds-tests-') as td:
 for name,modules in suites.items():
  exe=Path(td)/name
  cmd=[args.cc,'-std=c11','-Wall','-Wextra','-Werror','-g','-I',str(root/'source')]
  if not args.no_sanitizers:cmd+=['-fsanitize=address,undefined']
  cmd += [str(root/'tests'/(name+'.c'))]+[str(root/'source'/(m+'.c')) for m in modules]+['-o',str(exe)]
  subprocess.run(cmd,check=True)
  command=[str(exe)]+([str(Path(td)/'image.bmp')] if name=='image' else [])
  subprocess.run(command,check=True,env=env)
print('PASS: all nine asset-free portable suites')
