#include "save.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static uint8_t image[MDS_SAVE_SIZE],backup[MDS_SAVE_SIZE];
static MdsGallery g,h;
int main(void){MdsAvatar a;
 /* Every public gallery API must reject invalid pointers safely. */
 mds_gallery_new(NULL);
 assert(!mds_gallery_empty(NULL));
 mds_gallery_new(&g);assert(mds_gallery_empty(&g));
 assert(!mds_gallery_load(NULL,image,sizeof image));
 assert(!mds_gallery_load(&h,NULL,sizeof image));
 assert(!mds_gallery_store(NULL,0,&a));
 assert(!mds_gallery_store(&g,0,NULL));
 assert(!mds_gallery_delete(NULL,0));
 assert(!mds_gallery_commit(NULL,image,sizeof image));
 assert(!mds_gallery_commit(&g,NULL,sizeof image));memset(image,255,sizeof image);mds_gallery_new(&g);assert(!mds_gallery_load(&h,image,sizeof image));mds_new(&a);a.value[51]=1;assert(mds_gallery_store(&g,0,&a));assert(!mds_gallery_empty(&g));assert(!mds_gallery_delete(&g,0));assert(!mds_gallery_store(&g,1,&a));
 /* A corrupted in-memory gallery must never write two Personal Miis. */
 g.miis[1]=a;g.used[1]=1;
 uint32_t before_generation=g.generation;int before_bank=g.active_bank;
 assert(!mds_gallery_commit(&g,image,sizeof image));
 assert(g.generation==before_generation&&g.active_bank==before_bank);
 g.used[1]=0;
 a.value[51]=0;assert(!mds_gallery_store(&g,0,&a));for(unsigned i=1;i<100;i++){a.value[5]=(uint8_t)i;assert(mds_gallery_store(&g,i,&a));}assert(!mds_gallery_store(&g,100,&a));assert(mds_gallery_commit(&g,image,sizeof image));assert(mds_gallery_load(&h,image,sizeof image));assert(h.used[99]&&h.miis[99].value[5]==99);assert(mds_gallery_delete(&g,1));assert(mds_gallery_commit(&g,image,sizeof image));assert(mds_gallery_load(&h,image,sizeof image));assert(!h.used[1]);memcpy(backup,image,sizeof image);
 /* A torn new bank must fall back to the previous intact generation. */
 for(unsigned at=0;at<13528;at+=13){memcpy(image,backup,sizeof image);image[MDS_BANK_SIZE+at]^=1;assert(mds_gallery_load(&h,image,sizeof image));assert(h.used[1]);}
 /* A checksum-valid but logically impossible newest bank must NOT win over
  * its older consistent snapshot. Recompute the bank CRC to prove that
  * structural checks, not CRC failure alone, trigger recovery. */
 memset(image,255,sizeof image);
 mds_gallery_new(&g);mds_new(&a);a.value[51]=1;a.value[46]=1;
 assert(mds_gallery_store(&g,0,&a));
 assert(mds_gallery_commit(&g,image,sizeof image)); /* bank 0 / gen 1 */
 a.value[51]=0;a.value[46]=0;
 assert(mds_gallery_store(&g,1,&a));
 assert(mds_gallery_commit(&g,image,sizeof image)); /* bank 1 / gen 2 */
 assert(mds_gallery_load(&h,image,sizeof image));
 assert(h.active_bank==1&&h.generation==2&&h.used[1]);
 uint8_t *new_bank=image+MDS_BANK_SIZE;
 memcpy(new_bank+24+MDS_PACKET+1,new_bank+24,MDS_PACKET+1);
 uint32_t bad_crc=0xffffffffu;
 for(unsigned k=0;k<MDS_SAVE_BODY;k++){
  bad_crc^=new_bank[k];
  for(unsigned bit=0;bit<8;bit++)
   bad_crc=(bad_crc>>1)^(0xedb88320u&-(bad_crc&1u));
 }
 bad_crc=~bad_crc;
 for(unsigned k=0;k<4;k++)new_bank[MDS_SAVE_BODY+k]=(uint8_t)(bad_crc>>(k*8));
 assert(mds_gallery_load(&h,image,sizeof image));
 assert(h.active_bank==0&&h.generation==1&&h.used[0]&&!h.used[1]);
 assert(h.miis[0].value[51]);
 /* If BOTH banks violate the invariant, loading must fail and keep the
  * current in-memory gallery intact, rather than selecting either. */
 memcpy(image+24+MDS_PACKET+1,image+24,MDS_PACKET+1);
 bad_crc=0xffffffffu;
 for(unsigned k=0;k<MDS_SAVE_BODY;k++){
  bad_crc^=image[k];
  for(unsigned bit=0;bit<8;bit++)
   bad_crc=(bad_crc>>1)^(0xedb88320u&-(bad_crc&1u));
 }
 bad_crc=~bad_crc;
 for(unsigned k=0;k<4;k++)image[MDS_SAVE_BODY+k]=(uint8_t)(bad_crc>>(k*8));
 assert(!mds_gallery_load(&h,image,sizeof image));
 assert(h.active_bank==0&&h.generation==1&&h.used[0]&&!h.used[1]);
 memset(image,0,sizeof image);assert(!mds_gallery_load(&h,image,sizeof image));assert(!mds_gallery_load(&h,image,sizeof image-1));puts("PASS: 100 slots, personal protection, bank selection, torn-bank recovery, malformed images");}
