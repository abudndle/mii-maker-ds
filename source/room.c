#include "room.h"
#include "motion.h"
#include <stddef.h>
#include <string.h>\n#include "motion.h"
unsigned mds_room_start(unsigned selected)
{
 return selected<MDS_SLOTS?(selected/MDS_ROOM_SLOTS)*MDS_ROOM_SLOTS:0;
}
int mds_room_position(unsigned local,int *x,int *y)
{
 /* Original B_Mii_00...09 CLTY pane centers, with positive Y upward.
  * 3DS x = [-108,-54,0,54,108]; y = +30 first row, -30 second.
  * Mapping uses original 320x240 layout geometry, not invented positions. */
 static const int8_t source_x[5]={-108,-54,0,54,108};
 if(local>=MDS_ROOM_SLOTS||!x||!y)return 0;
 /* The source B_Mii panes are 52x58 around their origin.
  * Scale each ORIGINAL top-left edge, then round to DS pixels; rounding a
  * scaled center first is off by one pixel at both outer columns. */
 int src_left=160+source_x[local%5]-26;
 int src_top=120+(local<5?-30:30)-29;
 *x=(src_left*4+2)/5;
 *y=(src_top*4+2)/5;
 return 1;
}
void mds_room_select(MdsRoomCache *cache,unsigned selected)
{
 if(!cache||selected>=MDS_SLOTS)return;
 unsigned start=mds_room_start(selected);
 if(cache->start!=start){
  cache->start=start;
  for(unsigned i=0;i<MDS_ROOM_SLOTS;i++)cache->actor[i].valid=0;
 }
}
int mds_room_matches(const MdsRoomCache *cache,unsigned selected,unsigned local,const MdsAvatar *a)
{
 return cache&&a&&selected<MDS_SLOTS&&local<MDS_ROOM_SLOTS&&
   cache->start==mds_room_start(selected)&&cache->actor[local].valid&&
   memcmp(cache->actor[local].appearance,a->value,MDS_FIELDS)==0;
}
int mds_room_capture(MdsRoomCache *cache,unsigned selected,unsigned local,const MdsAvatar *a,const uint16_t *rendered)
{
 if(!cache||!a||!rendered||local>=MDS_ROOM_SLOTS||
    selected>=MDS_SLOTS||cache->start!=mds_room_start(selected))return 0;
 MdsRoomActor *actor=&cache->actor[local];
 actor->valid=0;
 for(unsigned y=0;y<MDS_ROOM_H;y++)
  for(unsigned x=0;x<MDS_ROOM_W;x++)
   actor->pixels[y*MDS_ROOM_W+x]=rendered[
       (y*MDS_ROOM_SOURCE/MDS_ROOM_H)*MDS_ROOM_SOURCE+
       (x*MDS_ROOM_SOURCE/MDS_ROOM_W)];
 memcpy(actor->appearance,a->value,MDS_FIELDS);
 actor->valid=1;
 return 1;
}
int mds_room_blit(const MdsRoomCache *cache,unsigned selected,unsigned local,uint16_t *dst,unsigned width,unsigned height,int x,int y)
{
 if(!dst||!width||!height||!cache||selected>=MDS_SLOTS||
    local>=MDS_ROOM_SLOTS||cache->start!=mds_room_start(selected)||
    !cache->actor[local].valid)return 0;
 /* Skip actors fully outside the destination without scanning their pixels. */
 if((int64_t)x+(int64_t)MDS_ROOM_W<=0||
    (int64_t)y+(int64_t)MDS_ROOM_H<=0||
    (int64_t)x>=(int64_t)width||(int64_t)y>=(int64_t)height)return 1;
 const MdsRoomActor *a=&cache->actor[local];
 for(unsigned j=0;j<MDS_ROOM_H;j++){
  int64_t dy=(int64_t)y+j;
  if(dy<0||(uint64_t)dy>=height)continue;
  for(unsigned i=0;i<MDS_ROOM_W;i++){
   int64_t dx=(int64_t)x+i;
   if(dx<0||(uint64_t)dx>=width)continue;
   uint16_t pixel=a->pixels[j*MDS_ROOM_W+i];
   if(pixel&0x8000u)dst[(size_t)dy*width+(unsigned)dx]=pixel;
  }
 }
 return 1;
}

int mds_room_next_refresh(const MdsRoomCache *cache,
 const uint8_t occupied[MDS_ROOM_SLOTS],
 const unsigned attempts[MDS_ROOM_SLOTS],unsigned cursor)
{
 if(!cache||!occupied||!attempts)return -1;
 for(unsigned i=0;i<MDS_ROOM_SLOTS;i++)
  if(occupied[i]&&!cache->actor[i].valid&&attempts[i]<3u)return -1;
 for(unsigned n=0;n<MDS_ROOM_SLOTS;n++){
  /* Reduce the cursor first: cursor + n may overflow on 32-bit ARM. */
  unsigned i=((cursor%MDS_ROOM_SLOTS)+n)%MDS_ROOM_SLOTS;
  if(occupied[i]&&cache->actor[i].valid&&attempts[i]<3u)return (int)i;
 }
 return -1;
}

void mds_room_walk_tick(MdsRoomWalk *walk,unsigned local,unsigned ticks,int return_home)
{
 if(!walk||local>=MDS_ROOM_SLOTS)return;
 if(return_home){walk->dx=0;walk->dy=0;walk->phase=0;return;}
 /* Stagger ten actors; move in a small loop around each assigned slot.
  * Fixed-point-free motion is reproducible on ARM9 and in host tests. */
 /* Reduce the elapsed time before adding the actor offset. This keeps
  * walking periodic and overflow-safe even after a long-running session. */
 unsigned phase=((ticks/12u)%64u+local*7u)%64u;
 int x=(int)(phase<16u?phase:phase<32u?16u:phase<48u?48u-phase:0u);
 int y=(int)(phase<16u?0u:phase<32u?phase-16u:phase<48u?16u:64u-phase);
 walk->dx=(int16_t)(x-8);
 walk->dy=(int16_t)(y-8);
 walk->phase=(uint8_t)phase;
}
