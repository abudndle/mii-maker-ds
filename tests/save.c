#include "save.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static uint8_t image[MDS_SAVE_SIZE],backup[MDS_SAVE_SIZE];
static MdsGallery g,h;
int main(void){MdsAvatar a;memset(image,255,sizeof image);mds_gallery_new(&g);assert(!mds_gallery_load(&h,image,sizeof image));mds_new(&a);a.value[51]=1;assert(mds_gallery_store(&g,0,&a));assert(!mds_gallery_delete(&g,0));assert(!mds_gallery_store(&g,1,&a));a.value[51]=0;assert(!mds_gallery_store(&g,0,&a));for(unsigned i=1;i<100;i++){a.value[5]=(uint8_t)i;assert(mds_gallery_store(&g,i,&a));}assert(!mds_gallery_store(&g,100,&a));assert(mds_gallery_commit(&g,image,sizeof image));assert(mds_gallery_load(&h,image,sizeof image));assert(h.used[99]&&h.miis[99].value[5]==99);assert(mds_gallery_delete(&g,1));assert(mds_gallery_commit(&g,image,sizeof image));assert(mds_gallery_load(&h,image,sizeof image));assert(!h.used[1]);memcpy(backup,image,sizeof image);
 /* A torn new bank must fall back to the previous intact generation. */
 for(unsigned at=0;at<13528;at+=13){memcpy(image,backup,sizeof image);image[MDS_BANK_SIZE+at]^=1;assert(mds_gallery_load(&h,image,sizeof image));assert(h.used[1]);}
 memset(image,0,sizeof image);assert(!mds_gallery_load(&h,image,sizeof image));assert(!mds_gallery_load(&h,image,sizeof image-1));puts("PASS: 100 slots, personal protection, bank selection, torn-bank recovery, malformed images");}
