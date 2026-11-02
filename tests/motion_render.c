/* Private integration gate: render original MSP1 poses using real CFL and
 * original BOD2 male/female meshes. No assets or image data are emitted. */
#include "head.h"
#include "motion.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_BODY_VERTICES 1440u
#define PREVIEW_PIXELS (128u*128u)
static uint16_t pixels[PREVIEW_PIXELS];

static uint8_t *read_file(const char *name,size_t *length)
{
 FILE *f=fopen(name,"rb");assert(f);
 assert(!fseek(f,0,SEEK_END));
 long size=ftell(f);assert(size>0 && size<16*1024*1024);
 rewind(f);
 uint8_t *data=malloc((size_t)size);assert(data);
 assert(fread(data,1,(size_t)size,f)==(size_t)size);
 assert(!fclose(f));
 *length=(size_t)size;
 return data;
}

static uint32_t digest(const void *bytes,size_t size)
{
 const uint8_t *p=bytes;uint32_t hash=2166136261u;
 for(size_t i=0;i<size;i++)hash=(hash^p[i])*16777619u;
 return hash;
}

int main(int argc,char **argv)
{
 /* CFL, MaleBody.bin, MaleBody.msp, FemaleBody.bin, FemaleBody.msp */
 assert(argc==6);
 size_t cfl_length;
 uint8_t *cfl_data=read_file(argv[1],&cfl_length);
 MdsCflArchive cfl;
 assert(mds_cfl_open(&cfl,cfl_data,cfl_length));
 const char *const idle[]={
  "Wait00","Wait01","Wait02","Wait03Pre","Wait03","Wait04"
 };
 unsigned total=0;
 for(unsigned gender=0;gender<2;gender++){
  size_t size;
  uint8_t *base=read_file(argv[2+gender*2],&size);
  assert(size>=56 && !memcmp(base,"BOD2",4));
  uint32_t vertices=(uint32_t)base[4]|(uint32_t)base[5]<<8|
                    (uint32_t)base[6]<<16|(uint32_t)base[7]<<24;
  assert(vertices>=3 && vertices<=MAX_BODY_VERTICES && !(vertices%3));
  assert(size==56+(size_t)vertices*12);
  size_t pose_length=56+(size_t)vertices*18;
  uint8_t *posed=malloc(pose_length);assert(posed);
  FILE *pack=fopen(argv[3+gender*2],"rb");assert(pack);
  MdsMotion motions={0};
  assert(mds_motion_open(&motions,pack));
  assert(motions.count==53);
  MdsAvatar avatar;mds_new(&avatar);
  avatar.value[0]=(uint8_t)gender;
  unsigned changed_mesh=0,changed_image=0,visible_frames=0;
  uint32_t baseline_mesh=0,baseline_image=0;
  for(unsigned n=0;n<sizeof idle/sizeof idle[0];n++){
   int clip=mds_motion_find(&motions,idle[n]);
   assert(clip>=0);
   uint32_t frames=motions.clips[clip].count;
   unsigned sample[3]={0u,frames/2u,frames-1u};
   for(unsigned k=0;k<3;k++){
    unsigned frame=sample[k];
    assert(mds_motion_pose(&motions,(unsigned)clip,frame,base,size,
                           posed,pose_length));
    assert(!memcmp(posed,"BOD3",4));
    uint32_t mesh=digest(posed,pose_length);
    assert(mds_mii_render(&cfl,&avatar,posed,pose_length,pixels,1)==1);
    uint32_t image=digest(pixels,sizeof pixels);
    unsigned visible=0;
    for(unsigned i=0;i<PREVIEW_PIXELS;i++)visible+=(pixels[i]&0x8000u)!=0u;
    assert(visible>1000u);
    if(!total || (gender==1 && n==0 && k==0)){
     baseline_mesh=mesh;baseline_image=image;
    }else{
     changed_mesh+=mesh!=baseline_mesh;
     changed_image+=image!=baseline_image;
    }
    visible_frames++;
   }
  }
  if(!changed_mesh || !changed_image){
   fprintf(stderr,"Original %s MSP1 idle pose/render variation is missing\n",
           gender?"female":"male");
   return 1;
  }
  printf("PASS: %s original MSP1 idle clips: %u rendered frames, pose/image variation verified\n",
         gender?"female":"male",visible_frames);
  total+=visible_frames;
  fclose(pack);
  free(posed);free(base);
 }
 free(cfl_data);
 printf("PASS: %u private original MSP1 animation frames rendered into complete Mii images\n",total);
 return 0;
}
