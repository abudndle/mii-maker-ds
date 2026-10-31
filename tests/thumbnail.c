#include "thumbnail.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static MdsThumbnailCache cache;
static uint16_t head[MDS_THUMBNAIL_SOURCE_SIDE*MDS_THUMBNAIL_SOURCE_SIDE];
static uint16_t canvas[MDS_THUMBNAIL_WIDTH*MDS_THUMBNAIL_HEIGHT];
int main(void)
{
 MdsAvatar a,b;mds_new(&a);b=a;
 assert(!mds_thumbnail_matches(NULL,0,0,&a));
 assert(!mds_thumbnail_matches(&cache,0,0,NULL));
 assert(!mds_thumbnail_capture(NULL,0,0,&a,head));
 assert(!mds_thumbnail_capture(&cache,0,0,NULL,head));
 assert(!mds_thumbnail_capture(&cache,0,0,&a,NULL));
 assert(!mds_thumbnail_capture(&cache,0,10,&a,head));
 mds_thumbnail_page(&cache,3);
 assert(!mds_thumbnail_matches(&cache,3,0,&a));
 assert(!mds_thumbnail_capture(&cache,2,0,&a,head));
 for(unsigned y=0;y<MDS_THUMBNAIL_SOURCE_SIDE;y++)
  for(unsigned x=0;x<MDS_THUMBNAIL_SOURCE_SIDE;x++)
   head[y*MDS_THUMBNAIL_SOURCE_SIDE+x]=(uint16_t)(0x8000u|((y&31u)<<5)|(x&31u));
 head[0]=0; /* Transparent pixels must leave original gallery artwork visible. */
 assert(mds_thumbnail_capture(&cache,3,4,&a,head));
 assert(mds_thumbnail_matches(&cache,3,4,&a));
 assert(!mds_thumbnail_matches(&cache,3,3,&a));
 assert(!mds_thumbnail_matches(&cache,2,4,&a));
 assert(!mds_thumbnail_matches(&cache,3,10,&a));
 /* Profile names and creator text do not alter face appearance. */
 strcpy(b.name,"Different");
 assert(mds_thumbnail_matches(&cache,3,4,&b));
 b.value[5]++;
 assert(!mds_thumbnail_matches(&cache,3,4,&b));
 b=a;
 for(unsigned i=0;i<MDS_THUMBNAIL_WIDTH*MDS_THUMBNAIL_HEIGHT;i++)canvas[i]=0x1234;
 assert(!mds_thumbnail_blit(&cache,3,4,NULL,MDS_THUMBNAIL_WIDTH,MDS_THUMBNAIL_HEIGHT,0,0));
 assert(!mds_thumbnail_blit(&cache,3,10,canvas,MDS_THUMBNAIL_WIDTH,MDS_THUMBNAIL_HEIGHT,0,0));
 assert(mds_thumbnail_blit(&cache,3,4,canvas,MDS_THUMBNAIL_WIDTH,MDS_THUMBNAIL_HEIGHT,0,0));
 assert(canvas[0]==0x1234);
 unsigned sx=(MDS_THUMBNAIL_WIDTH-1)*MDS_THUMBNAIL_SOURCE_SIDE/MDS_THUMBNAIL_WIDTH;
 unsigned sy=(MDS_THUMBNAIL_HEIGHT-1)*MDS_THUMBNAIL_SOURCE_SIDE/MDS_THUMBNAIL_HEIGHT;
 assert(canvas[MDS_THUMBNAIL_WIDTH*MDS_THUMBNAIL_HEIGHT-1]==head[sy*MDS_THUMBNAIL_SOURCE_SIDE+sx]);
 /* Edge-clipped blits must never write outside the provided bitmap. */
 for(unsigned i=0;i<MDS_THUMBNAIL_WIDTH*MDS_THUMBNAIL_HEIGHT;i++)canvas[i]=0x1234;
 assert(mds_thumbnail_blit(&cache,3,4,canvas,MDS_THUMBNAIL_WIDTH,MDS_THUMBNAIL_HEIGHT,41,45));
 assert(canvas[0]==0x1234);
 assert(canvas[MDS_THUMBNAIL_WIDTH*MDS_THUMBNAIL_HEIGHT-1]==0x1234); /* top-left sample is transparent */
 assert(mds_thumbnail_blit(&cache,3,4,canvas,MDS_THUMBNAIL_WIDTH,MDS_THUMBNAIL_HEIGHT,-40,-44));
 assert(canvas[1+MDS_THUMBNAIL_WIDTH]==head[45*MDS_THUMBNAIL_SOURCE_SIDE/ MDS_THUMBNAIL_HEIGHT * MDS_THUMBNAIL_SOURCE_SIDE + 41*MDS_THUMBNAIL_SOURCE_SIDE/MDS_THUMBNAIL_WIDTH]);
 mds_thumbnail_page(&cache,4);
 assert(!mds_thumbnail_matches(&cache,4,4,&a)); /* New page is always invalidated. */
 assert(!mds_thumbnail_matches(&cache,3,4,&a));
 assert(!mds_thumbnail_blit(&cache,3,4,canvas,MDS_THUMBNAIL_WIDTH,MDS_THUMBNAIL_HEIGHT,0,0));
 assert(mds_thumbnail_capture(&cache,4,4,&a,head));
 assert(mds_thumbnail_matches(&cache,4,4,&a));
 puts("PASS: gallery thumbnail cache, 62-field invalidation, transparency, scaling, clipping, page changes");
}
