#include "animation.h"
#include "head.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static uint16_t pixels[128*128];
static void*load(const char*path,size_t*n){FILE*f=fopen(path,"rb");assert(f);assert(!fseek(f,0,SEEK_END));*n=(size_t)ftell(f);rewind(f);void*p=malloc(*n);assert(p);assert(fread(p,1,*n,f)==*n);fclose(f);return p;}
static unsigned hash(void){unsigned h=2166136261u;for(unsigned i=0;i<128*128;i++)h=(h^pixels[i])*16777619u;return h;}
static int abort_render(void){return 1;}
int main(int argc,char**argv){
 assert(argc==4);size_t n;void*bytes=load(argv[1],&n);MdsCflArchive cfl;assert(mds_cfl_open(&cfl,bytes,n));
 for(int gender=0;gender<2;gender++){
  size_t size;uint8_t*b=load(argv[gender+2],&size);MdsAnimation a,bad;assert(mds_animation_open(&a,b,size));assert(a.count==24&&a.period==120&&a.step==5&&a.fps==30);
  MdsAvatar m;mds_new(&m);m.value[0]=gender;unsigned first=0,different=0;
  for(unsigned i=0;i<a.count;i++){
   unsigned index;const void*p=mds_animation_pose(&a,i*10,&index);assert(index==i);assert(mds_mii_render(&cfl,&m,p,a.pose_bytes,pixels,1));
   unsigned h=hash();if(!i)first=h;else different+=h!=first;
  }
  assert(different>12);
  mds_render_set_abort(abort_render);assert(mds_mii_render(&cfl,&m,a.data,a.pose_bytes,pixels,1)==-1);mds_render_set_abort(NULL);assert(mds_mii_render(&cfl,&m,a.data,a.pose_bytes,pixels,1)==1);
  assert(mds_animation_pose(&a,240,NULL)==a.data);
  assert(mds_animation_pose(&a,UINT32_MAX,NULL));
  assert(!mds_animation_open(&bad,b,size-1));assert(!mds_animation_open(&bad,b,23));
  uint8_t old=b[24+a.pose_bytes];b[24+a.pose_bytes]=0;assert(!mds_animation_open(&bad,b,size));b[24+a.pose_bytes]=old;
  old=b[8];b[8]=0;assert(!mds_animation_open(&bad,b,size));b[8]=old;
  assert(!mds_animation_pose(&bad,0,NULL));free(b);
 }
 free(bytes);puts("PASS: all original male/female sampled poses render, timing/wrap, long clock, malformed/truncated animation rejected");
}
