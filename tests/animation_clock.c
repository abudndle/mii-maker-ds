#include "animation.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static void word(uint8_t *p, unsigned v) {
 for (unsigned i=0;i<4;i++) p[i]=(uint8_t)(v>>(8*i));
}
int main(void) {
 /* Three minimal original-format BOD2 poses: source-free timing fixture. */
 uint8_t pack[24+3*56]={0};
 memcpy(pack,"ANI1",4);
 word(pack+4,3);word(pack+8,56);word(pack+12,6);word(pack+16,2);word(pack+20,30);
 for(unsigned i=0;i<3;i++)memcpy(pack+24+i*56,"BOD2",4);
 MdsAnimation anim;
 assert(mds_animation_open(&anim,pack,sizeof pack));
 assert(anim.count==3&&anim.pose_bytes==56);
 unsigned index=99;
 assert(mds_animation_pose(&anim,0,&index)==pack+24&&index==0);
 assert(mds_animation_pose(&anim,4,&index)==pack+80&&index==1);
 assert(mds_animation_pose(&anim,8,&index)==pack+136&&index==2);
 assert(mds_animation_pose(&anim,12,&index)==pack+24&&index==0);
 assert(mds_animation_pose(&anim,UINT32_MAX,&index)!=NULL&&index<3);
 assert(!mds_animation_open(&anim,pack,sizeof pack-1));
 assert(!mds_animation_pose(&anim,0,NULL));
 puts("PASS: asset-free original pose timing, wrap and truncated animation guard");
 return 0;
}
