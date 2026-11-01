#include "thumbnail.h"
#include <string.h>
void mds_thumbnail_page(MdsThumbnailCache *cache,unsigned page)
{
 if(!cache||page>=10||cache->page==page)return;
 for(unsigned i=0;i<MDS_THUMBNAIL_SLOTS;i++)cache->slots[i].valid=0;
 cache->page=page;
}
int mds_thumbnail_matches(const MdsThumbnailCache *cache,unsigned page,unsigned local,const MdsAvatar *avatar)
{
 return cache&&avatar&&page<10&&cache->page==page&&local<MDS_THUMBNAIL_SLOTS&&
  cache->slots[local].valid&&
  !memcmp(cache->slots[local].appearance,avatar->value,MDS_FIELDS);
}
int mds_thumbnail_capture(MdsThumbnailCache *cache,unsigned page,unsigned local,const MdsAvatar *avatar,const uint16_t *head)
{
 if(!cache||!avatar||!head||page>=10||cache->page!=page||local>=MDS_THUMBNAIL_SLOTS)return 0;
 MdsThumbnail *thumb=&cache->slots[local];
 thumb->valid=0;
 for(unsigned y=0;y<MDS_THUMBNAIL_HEIGHT;y++)
  for(unsigned x=0;x<MDS_THUMBNAIL_WIDTH;x++)
   thumb->pixels[y*MDS_THUMBNAIL_WIDTH+x]=
    head[(y*MDS_THUMBNAIL_SOURCE_SIDE/MDS_THUMBNAIL_HEIGHT)*MDS_THUMBNAIL_SOURCE_SIDE+
         x*MDS_THUMBNAIL_SOURCE_SIDE/MDS_THUMBNAIL_WIDTH];
 memcpy(thumb->appearance,avatar->value,MDS_FIELDS);
 thumb->valid=1;
 return 1;
}
int mds_thumbnail_blit(const MdsThumbnailCache *cache,unsigned page,unsigned local,uint16_t *dest,unsigned width,unsigned height,int x,int y)
{
 if(!cache||!dest||page>=10||cache->page!=page||local>=MDS_THUMBNAIL_SLOTS||
    !cache->slots[local].valid||!width||!height)return 0;
 const MdsThumbnail *thumb=&cache->slots[local];
 for(unsigned j=0;j<MDS_THUMBNAIL_HEIGHT;j++){
  int64_t dy=(int64_t)y+j;if(dy<0||(uint64_t)dy>=height)continue;
  for(unsigned i=0;i<MDS_THUMBNAIL_WIDTH;i++){
   int64_t dx=(int64_t)x+i;if(dx<0||(uint64_t)dx>=width)continue;
   uint16_t pixel=thumb->pixels[j*MDS_THUMBNAIL_WIDTH+i];
   if(pixel&0x8000u)dest[(size_t)dy*width+(unsigned)dx]=pixel;
  }
 }
 return 1;
}
