#include "room.h"
#include <assert.h>
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
 assert(mds_room_start(4)==0);
 assert(mds_room_start(5)==5);
 assert(mds_room_start(99)==95);
 for(unsigned i=0;i<MDS_ROOM_SOURCE*MDS_ROOM_SOURCE;i++)rendered[i]=0x801fu;
 mds_room_select(&cache,9);
 assert(cache.start==5);
 assert(!mds_room_matches(&cache,9,0,&a));
 assert(mds_room_capture(&cache,9,0,&a,rendered));
 assert(mds_room_matches(&cache,9,0,&a));
 assert(mds_room_blit(&cache,9,0,dst,256,192,-9,0));
 assert(dst[0]==0x801f);
 a.value[5]++;
 assert(!mds_room_matches(&cache,9,0,&a));
 mds_room_select(&cache,10);
 assert(cache.start==10);
 assert(!cache.actor[0].valid);
 assert(!mds_room_capture(&cache,10,5,&a,rendered));
 assert(!mds_room_blit(&cache,10,5,dst,256,192,0,0));
 assert(!mds_room_capture(NULL,10,0,&a,rendered));
 assert(!mds_room_blit(NULL,10,0,dst,256,192,0,0));
 puts("PASS: five-Mii room positions, independent cached model images, invalidation and clipping");
 return 0;
}
