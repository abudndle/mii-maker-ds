#include "room.h"
#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>
int main(void)
{
 static MdsRoomCache cache;
 static uint16_t rendered[MDS_ROOM_SOURCE*MDS_ROOM_SOURCE];
 static uint16_t dst[256*192];
 MdsAvatar a;
 memset(&a,0,sizeof a);
 memset(&cache,0,sizeof cache);
 assert(mds_room_start(0)==0);
 int x=0,y=0;
 const int expected_x[10]={21,64,107,150,194,21,64,107,150,194};
 for(unsigned i=0;i<10;i++){
  assert(mds_room_position(i,&x,&y));
  assert(x==expected_x[i]);
  assert(y==(i<5?49:97));
 }
 assert(!mds_room_position(10,&x,&y));
 assert(!mds_room_position(0,NULL,&y));
 assert(mds_room_start(4)==0);
 assert(mds_room_start(5)==0);
 assert(mds_room_start(9)==0);
 assert(mds_room_start(10)==10);
 assert(mds_room_start(99)==90);
 for(unsigned i=0;i<MDS_ROOM_SOURCE*MDS_ROOM_SOURCE;i++)rendered[i]=0x801fu;
 mds_room_select(&cache,19);
 assert(cache.start==10);
 assert(!mds_room_matches(&cache,19,0,&a));
 assert(mds_room_capture(&cache,19,0,&a,rendered));
 assert(mds_room_matches(&cache,19,0,&a));
 /* Room cache identity is based on appearance, not slot selection. */
 assert(mds_room_matches(&cache,10,0,&a));
 assert(!mds_room_matches(&cache,9,0,&a));
 assert(!mds_room_matches(&cache,19,1,&a));
 assert(mds_room_blit(&cache,19,0,dst,256,192,-9,0));
 assert(dst[0]==0x801f);
 /* Extreme placement must not wrap onto the opposite edge of the room. */
 dst[0]=0;
 assert(mds_room_blit(&cache,19,0,dst,256,192,INT_MAX,0));
 assert(dst[0]==0);
 assert(mds_room_blit(&cache,19,0,dst,256,192,0,INT_MAX));
 assert(dst[0]==0);
 assert(mds_room_blit(&cache,19,0,dst,256,192,INT_MIN,0));
 assert(dst[0]==0);
 assert(mds_room_blit(&cache,19,0,dst,256,192,0,INT_MIN));
 assert(dst[0]==0);
 /* Transparent pixels preserve the scene and neighboring actors. */
 for(unsigned i=0;i<MDS_ROOM_SOURCE*MDS_ROOM_SOURCE;i++)rendered[i]=0;
 rendered[0]=0x83e0u;
 assert(mds_room_capture(&cache,19,2,&a,rendered));
 for(unsigned i=0;i<256u*192u;i++)dst[i]=0x801fu;
 assert(mds_room_blit(&cache,19,2,dst,256,192,20,20));
 assert(dst[20u*256u+20u]==0x83e0u);
 assert(dst[20u*256u+21u]==0x801fu);
 assert(dst[19u*256u+20u]==0x801fu);
 /* Two cached actors can be drawn without overwriting each other's pixels. */
 assert(mds_room_blit(&cache,19,0,dst,256,192,100,20));
 assert(dst[20u*256u+100u]==0x801fu);
 assert(dst[20u*256u+20u]==0x83e0u);
 a.value[5]++;
 assert(!mds_room_matches(&cache,19,0,&a));
 assert(mds_room_capture(&cache,19,1,&a,rendered));
 assert(mds_room_matches(&cache,19,1,&a));
 /* Selecting a different slot in the same room retains all cached Miis. */
 mds_room_select(&cache,10);
 assert(cache.actor[0].valid);
 assert(cache.actor[1].valid);
 assert(cache.actor[2].valid);
 mds_room_select(&cache,20);
 assert(cache.start==20);
 assert(!cache.actor[0].valid);
 assert(!mds_room_capture(&cache,20,10,&a,rendered));
 assert(!mds_room_blit(&cache,20,10,dst,256,192,0,0));
 assert(!mds_room_capture(NULL,20,0,&a,rendered));
 assert(!mds_room_blit(NULL,20,0,dst,256,192,0,0));
 puts("PASS: source-derived ten-Mii room positions, independent cached model images, invalidation and clipping");
 return 0;
}
