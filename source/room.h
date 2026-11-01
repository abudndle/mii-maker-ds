#ifndef MDS_ROOM_MODULE_H
#define MDS_ROOM_MODULE_H
#include "save.h"
#include <stdint.h>
#define MDS_ROOM_SLOTS 10u
#define MDS_ROOM_W 42u
#define MDS_ROOM_H 46u
#define MDS_ROOM_SOURCE 128u
typedef struct {
 uint8_t appearance[MDS_FIELDS];
 uint16_t pixels[MDS_ROOM_W*MDS_ROOM_H];
 uint8_t valid;
} MdsRoomActor;
typedef struct {
 unsigned start;
 MdsRoomActor actor[MDS_ROOM_SLOTS];
} MdsRoomCache;
/* Ten source-layout Mii positions form each 3DS SelectMii room. */
typedef struct { int16_t dx,dy; uint8_t phase; } MdsRoomWalk;
/* Deterministic bounded wandering; return_home immediately resets displacement. */
void mds_room_walk_tick(MdsRoomWalk *walk,unsigned local,unsigned ticks,int return_home);
unsigned mds_room_start(unsigned selected);
/* Source: Select.arc.files/blyt/SelectMii, 320x240 canvas to DS 256x192. */
int mds_room_position(unsigned local,int *x,int *y);
/* Touch hit test for room actor sprites, frontmost actor first. */
int mds_room_hit(const uint8_t occupied[MDS_ROOM_SLOTS],const MdsRoomWalk walk[MDS_ROOM_SLOTS],int x,int y);
void mds_room_select(MdsRoomCache *,unsigned selected);
int mds_room_matches(const MdsRoomCache *,unsigned selected,unsigned local,const MdsAvatar *);
int mds_room_capture(MdsRoomCache *,unsigned selected,unsigned local,const MdsAvatar *,const uint16_t *rendered);
int mds_room_blit(const MdsRoomCache *,unsigned selected,unsigned local,uint16_t *dst,unsigned width,unsigned height,int x,int y);
/* Choose the next occupied cached actor to animate, or -1 while any
 * renderable occupied slot still awaits its first preview. */
int mds_room_next_refresh(const MdsRoomCache *cache,
 const uint8_t occupied[MDS_ROOM_SLOTS],
 const unsigned attempts[MDS_ROOM_SLOTS],unsigned cursor);
#endif
