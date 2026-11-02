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
 /* Refresh scheduling must not starve unseen Miis or empty slots. */
 uint8_t occupied[MDS_ROOM_SLOTS]={0};
 unsigned attempts[MDS_ROOM_SLOTS]={0};
 memset(&cache,0,sizeof cache);
 occupied[1]=1;occupied[4]=1;
 cache.actor[1].valid=1;
 assert(mds_room_next_refresh(&cache,occupied,attempts,0)==-1);
 cache.actor[4].valid=1;
 assert(mds_room_next_refresh(&cache,occupied,attempts,0)==1);
 assert(mds_room_next_refresh(&cache,occupied,attempts,2)==4);
 assert(mds_room_next_refresh(&cache,occupied,attempts,5)==1);
 attempts[1]=3;
 assert(mds_room_next_refresh(&cache,occupied,attempts,0)==4);
 cache.actor[4].valid=0;
 assert(mds_room_next_refresh(&cache,occupied,attempts,0)==-1);
 attempts[4]=3;
 assert(mds_room_next_refresh(&cache,occupied,attempts,0)==-1);
 assert(mds_room_next_refresh(NULL,occupied,attempts,0)==-1);
 assert(mds_room_next_refresh(&cache,NULL,attempts,0)==-1);
 assert(mds_room_next_refresh(&cache,occupied,NULL,0)==-1);
 /* A retry-exhausted missing actor must not block a healthy cached actor. */
 occupied[7]=1;
 cache.actor[7].valid=1;
 assert(mds_room_next_refresh(&cache,occupied,attempts,0)==7);
 assert(mds_room_next_refresh(&cache,occupied,attempts,8)==7);
 /* An occupied uncached actor with attempts remaining takes priority. */
 occupied[9]=1;
 assert(mds_room_next_refresh(&cache,occupied,attempts,0)==-1);
 attempts[9]=3;
 assert(mds_room_next_refresh(&cache,occupied,attempts,0)==7);
 /* The cursor can wrap even if it is larger than the room size. */
 assert(mds_room_next_refresh(&cache,occupied,attempts,1007)==7);
 /* Large unsigned cursors must wrap deterministically without overflow. */
 assert(mds_room_next_refresh(&cache,occupied,attempts,UINT_MAX)==7);
 assert(mds_room_next_refresh(&cache,occupied,attempts,UINT_MAX-1u)==7);
 /* Walking stays inside a small bounded area and resets on demand. */
 MdsRoomWalk walks[MDS_ROOM_SLOTS]={0};
 for(unsigned tick=0;tick<768;tick++){
  for(unsigned slot=0;slot<MDS_ROOM_SLOTS;slot++){
   mds_room_walk_tick(&walks[slot],slot,tick,0);
   assert(walks[slot].dx>=-8&&walks[slot].dx<=8);
   assert(walks[slot].dy>=-8&&walks[slot].dy<=8);
  }
 }
 /* Walking remains periodic across long sessions and near tick rollover. */
 for(unsigned slot=0;slot<MDS_ROOM_SLOTS;slot++){
  MdsRoomWalk first={0}, repeated={0};
  mds_room_walk_tick(&first,slot,UINT_MAX-768u,0);
  mds_room_walk_tick(&repeated,slot,UINT_MAX,0);
  assert(first.dx==repeated.dx&&first.dy==repeated.dy&&first.phase==repeated.phase);
  mds_room_walk_tick(&repeated,slot,UINT_MAX-1u,0);
  assert(repeated.dx>=-8&&repeated.dx<=8);
  assert(repeated.dy>=-8&&repeated.dy<=8);
 }
 assert(walks[0].phase!=walks[1].phase);
 for(unsigned slot=0;slot<MDS_ROOM_SLOTS;slot++){
  mds_room_walk_tick(&walks[slot],slot,768,1);
  assert(walks[slot].dx==0&&walks[slot].dy==0&&walks[slot].phase==0);
 }
 mds_room_walk_tick(NULL,0,0,0);
 mds_room_walk_tick(&walks[0],MDS_ROOM_SLOTS,0,0);
 assert(walks[0].dx==0&&walks[0].dy==0);
 puts("PASS: source-derived ten-Mii room positions, independent cached model images, invalidation and clipping");
 return 0;
}
