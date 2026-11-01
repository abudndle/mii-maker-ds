#ifndef MDS_ROOM_H
#define MDS_ROOM_H
#include "avatar.h"
#include <stdint.h>
#define MDS_ROOM_SLOTS 5u
#define MDS_ROOM_W 46u
#define MDS_ROOM_H 84u
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
/* Five saved Miis occupy one scene; changing selection halves switches room. */
unsigned mds_room_start(unsigned selected);
void mds_room_select(MdsRoomCache *,unsigned selected);
int mds_room_matches(const MdsRoomCache *,unsigned selected,unsigned local,const MdsAvatar *);
int mds_room_capture(MdsRoomCache *,unsigned selected,unsigned local,const MdsAvatar *,const uint16_t *rendered);
int mds_room_blit(const MdsRoomCache *,unsigned selected,unsigned local,uint16_t *dst,unsigned width,unsigned height,int x,int y);
#endif
