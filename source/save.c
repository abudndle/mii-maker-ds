#include "save.h"
#include <string.h>
#define BODY MDS_SAVE_BODY
static uint32_t checksum(const uint8_t *p,size_t n){uint32_t c=~0u;for(size_t i=0;i<n;i++){c^=p[i];for(int k=0;k<8;k++)c=(c>>1)^(0xedb88320u&-(c&1));}return ~c;}
static uint32_t get(const uint8_t *p){return p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static void put(uint8_t *p,uint32_t v){for(int i=0;i<4;i++)p[i]=(uint8_t)(v>>(i*8));}
void mds_gallery_new(MdsGallery *g){if(!g)return;memset(g,0,sizeof *g);g->active_bank=-1;}
int mds_gallery_empty(const MdsGallery *g)
{
 if(!g)return 0;
 for(unsigned i=0;i<MDS_SLOTS;i++)if(g->used[i])return 0;
 return 1;
}
static int valid(const uint8_t *p)
{
 if(memcmp(p,"MDSV",4)||get(p+4)!=1||get(p+12)!=BODY||
    get(p+BODY)!=checksum(p,BODY))return 0;
 unsigned personal=0;
 for(unsigned i=0;i<MDS_SLOTS;i++){
  const uint8_t *s=p+24+i*(MDS_PACKET+1);
  if(s[0]>1)return 0;
  if(s[0]){
   MdsAvatar a;
   if(!mds_decode(&a,s+1,MDS_PACKET))return 0;
   /* A bank can have a correct CRC and 100 individually valid records,
    * yet violate the gallery's single Personal Mii invariant. Invalidate
    * the entire bank so the loader can recover from its older snapshot. */
   if(a.value[51]&&++personal>1)return 0;
  }
 }
 return 1;
}
int mds_gallery_load(MdsGallery *g,const uint8_t *image,size_t n){if(!g||!image||n!=MDS_SAVE_SIZE)return 0;int a=valid(image),b=valid(image+MDS_BANK_SIZE),bank;if(!a&&!b)return 0;if(a&&b){uint32_t delta=get(image+MDS_BANK_SIZE+8)-get(image+8);bank=delta!=0&&delta<0x80000000u;}else bank=b?1:0;const uint8_t *p=image+bank*MDS_BANK_SIZE;mds_gallery_new(g);g->active_bank=bank;g->generation=get(p+8);memcpy(g->settings,p+16,8);for(unsigned i=0;i<MDS_SLOTS;i++){const uint8_t *s=p+24+i*(MDS_PACKET+1);g->used[i]=s[0];if(s[0])mds_decode(&g->miis[i],s+1,MDS_PACKET);}return 1;}
int mds_gallery_store(MdsGallery *g,unsigned slot,const MdsAvatar *a){if(!g||slot>=MDS_SLOTS||!mds_valid(a))return 0;for(unsigned i=0;i<MDS_SLOTS;i++)if(i!=slot&&g->used[i]&&g->miis[i].value[51]&&a->value[51])return 0;if(g->used[slot]&&g->miis[slot].value[51]&&!a->value[51])return 0;g->miis[slot]=*a;g->used[slot]=1;return 1;}
int mds_gallery_delete(MdsGallery *g,unsigned slot){if(!g||slot>=MDS_SLOTS||!g->used[slot]||g->miis[slot].value[51])return 0;g->used[slot]=0;memset(&g->miis[slot],0,sizeof g->miis[slot]);return 1;}
int mds_gallery_commit(MdsGallery *g,uint8_t *image,size_t n){if(!g||!image||n!=MDS_SAVE_SIZE)return 0;unsigned personal=0;for(unsigned i=0;i<MDS_SLOTS;i++){if(g->used[i]>1||(g->used[i]&&!mds_valid(&g->miis[i])))return 0;if(g->used[i]&&g->miis[i].value[51]&&++personal>1)return 0;}int bank=g->active_bank==0?1:0;uint8_t *p=image+bank*MDS_BANK_SIZE;memset(p,0xff,MDS_BANK_SIZE);memcpy(p,"MDSV",4);put(p+4,1);put(p+8,g->generation+1);put(p+12,BODY);memcpy(p+16,g->settings,8);for(unsigned i=0;i<MDS_SLOTS;i++){uint8_t *s=p+24+i*(MDS_PACKET+1);s[0]=g->used[i];if(s[0])mds_encode(&g->miis[i],s+1,MDS_PACKET);}put(p+BODY,checksum(p,BODY));g->generation++;g->active_bank=bank;return 1;}
